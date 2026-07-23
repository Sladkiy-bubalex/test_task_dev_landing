import psutil
import os
from fastapi import APIRouter
from loguru import logger
from datetime import datetime
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint with system information"""
    logger.info("Health check requested")

    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        health_data = {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "system": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%",
                "python_version": os.sys.version,
            },
            "checks": {
                "mistral_configured": bool(settings.MISTRAL_API_KEY),
                "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USER),
                "data_directory_writable": os.access(settings.DATA_DIR, os.W_OK),
            },
        }

        logger.debug(f"Health check completed: {health_data['status']}")

        return health_data

    except Exception as e:
        logger.exception(f"Health check failed: {str(e)}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
