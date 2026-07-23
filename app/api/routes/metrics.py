from fastapi import APIRouter, HTTPException, status
from loguru import logger
import json
import aiofiles
from datetime import datetime
from app.config import settings

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """Get API metrics and statistics"""
    logger.info("Metrics requested")

    try:
        metrics_path = f"{settings.DATA_DIR}/metrics.json"

        async with aiofiles.open(metrics_path, "r") as f:
            content = await f.read()
            metrics = json.loads(content)

        logger.info(
            f"Metrics loaded: {metrics.get('total_requests', 0)} total requests"
        )

        # Add system metrics
        metrics["system"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "see health endpoint for uptime",
        }

        return metrics

    except FileNotFoundError:
        logger.warning("Metrics file not found - returning empty metrics")
        return {
            "total_requests": 0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "daily_stats": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "category_distribution": {},
            "message": "No metrics available yet",
        }

    except Exception as e:
        logger.exception(f"Failed to load metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load metrics",
        )
