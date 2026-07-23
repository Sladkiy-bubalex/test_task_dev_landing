from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""

    # Get request details
    method = request.method
    url = request.url.path
    client = request.client.host if request.client else "unknown"

    # Log with appropriate level
    if isinstance(exc, HTTPException):
        if exc.status_code >= 500:
            logger.error(
                f"HTTP {exc.status_code} on {method} {url} | "
                f"Client: {client} | Detail: {exc.detail}"
            )
        else:
            logger.warning(
                f"HTTP {exc.status_code} on {method} {url} | "
                f"Client: {client} | Detail: {exc.detail}"
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "type": "http_error"},
        )

    # For validation errors
    if hasattr(exc, "errors"):
        logger.warning(
            f"Validation error on {method} {url} | "
            f"Client: {client} | Errors: {exc.errors()}"
        )

        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()},
        )

    # Generic error response
    logger.exception(
        f"Unhandled exception on {method} {url} | "
        f"Client: {client} | Type: {type(exc).__name__}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
