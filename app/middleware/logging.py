import sys
import os
import json
from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import traceback
from app.config import settings


def setup_logging():
    """Configure loguru logging for the application"""

    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    os.makedirs(settings.LOGS_DIR, exist_ok=True)

    # Log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
        enqueue=True,
    )

    # File handler for all logs
    logger.add(
        f"{settings.LOGS_DIR}/app.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        enqueue=True,
    )

    # Error-specific log file
    logger.add(
        f"{settings.LOGS_DIR}/errors.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="gz",
        encoding="utf-8",
        enqueue=True,
    )

    # Intercept standard logging
    import logging as std_logging

    class InterceptHandler(std_logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = std_logging.currentframe(), 2
            while frame and frame.f_code.co_filename == std_logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    std_logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set specific log levels for noisy libraries
    for lib in ["openai", "httpx", "urllib3", "asyncio", "mistralai"]:
        std_logging.getLogger(lib).setLevel(std_logging.WARNING)

    logger.info("Logging configured successfully")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{id(request)}"

        # Log request
        logger.info(
            f"[{request_id}] Request: {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        start_time = datetime.now()

        try:
            response = await call_next(request)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Log response
            if response.status_code >= 500:
                logger.error(
                    f"[{request_id}] Response: {response.status_code} | "
                    f"Duration: {duration:.2f}ms"
                )
            elif response.status_code >= 400:
                logger.warning(
                    f"[{request_id}] Response: {response.status_code} | "
                    f"Duration: {duration:.2f}ms"
                )
            else:
                logger.info(
                    f"[{request_id}] Response: {response.status_code} | "
                    f"Duration: {duration:.2f}ms"
                )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.exception(
                f"[{request_id}] Request failed | Duration: {duration:.2f}ms | Error: {str(e)}"
            )
            raise
