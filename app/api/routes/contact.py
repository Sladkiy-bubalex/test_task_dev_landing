from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from app.models.contact import ContactRequest, ContactResponse
from app.services.contact_service import ContactService
from app.services.rate_limiter import RateLimiter
from app.config import settings

router = APIRouter()

rate_limiter = RateLimiter()
contact_service = ContactService()


async def get_client_id(request: Request) -> str:
    """Get unique client identifier for rate limiting"""
    forwarded = request.headers.get("X-Forwarded-For")
    client_id = forwarded.split(",")[0] if forwarded else request.client.host
    logger.debug(f"Client ID resolved: {client_id}")
    return client_id


@router.post(
    "/contact",
    response_model=ContactResponse,
    summary="Submit contact form",
    description="Submit a contact form with name, phone, email, and optional comment",
    response_description="Contact submission response with AI analysis",
    status_code=status.HTTP_200_OK,
)
async def submit_contact(
    contact: ContactRequest, request: Request, client_id: str = Depends(get_client_id)
):
    """
    Submit a contact form:

    - **name**: Full name (2-100 characters, letters only)
    - **phone**: Phone number (10-20 digits, will be formatted)
    - **email**: Valid email address
    - **comment**: Optional message (max 1000 characters)
    """

    logger.info(f"Contact form submission from {contact.email} (IP: {client_id})")

    # Rate limiting
    allowed, limit_info = await rate_limiter.check_rate_limit(client_id)
    if not allowed:
        retry_after = limit_info.get("retry_after", 3600)
        logger.warning(
            f"Rate limit blocked request from {client_id} | "
            f"Retry after: {retry_after}s"
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after,
                "limit": limit_info.get("limit", settings.RATE_LIMIT_MAX_REQUESTS),
            },
            headers={"Retry-After": str(retry_after)},
        )

    try:
        # Log rate limit info
        logger.debug(f"Rate limit info: {limit_info}")

        # Process contact
        result = await contact_service.process_contact(contact)

        logger.success(f"Contact processed successfully for {contact.email}")

        return ContactResponse(**result)

    except Exception as e:
        logger.exception(f"Contact submission failed for {contact.email}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing your request",
        )
