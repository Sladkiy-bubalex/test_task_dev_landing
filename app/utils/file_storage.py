import json
import aiofiles
import os
from datetime import datetime
from loguru import logger
from app.config import settings


class FileStorage:
    def __init__(self):
        self.metrics_path = f"{settings.DATA_DIR}/metrics.json"
        self._ensure_files_exist()
        logger.info(f"File storage initialized at {settings.DATA_DIR}")

    def _ensure_files_exist(self):
        """Ensure required files and directories exist"""
        os.makedirs(settings.DATA_DIR, exist_ok=True)

        if not os.path.exists(self.metrics_path):
            self._create_default_metrics()
            logger.info(f"Created default metrics file at {self.metrics_path}")

    def _create_default_metrics(self):
        """Create default metrics structure"""
        default_metrics = {
            "total_requests": 0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "daily_stats": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "category_distribution": {},
            "last_updated": datetime.utcnow().isoformat(),
        }

        with open(self.metrics_path, "w") as f:
            json.dump(default_metrics, f, indent=2)

    async def update_metrics(self, data: dict):
        """Update metrics with new submission data"""
        logger.debug("Updating metrics with new data")

        try:
            # Load current metrics
            metrics = await self._load_json(self.metrics_path)

            # Update counters
            metrics["total_requests"] = metrics.get("total_requests", 0) + 1

            if data.get("success"):
                metrics["successful_submissions"] = (
                    metrics.get("successful_submissions", 0) + 1
                )
            else:
                metrics["failed_submissions"] = metrics.get("failed_submissions", 0) + 1

            # Update sentiment distribution
            sentiment = data.get("sentiment", "neutral")
            metrics["sentiment_distribution"][sentiment] = (
                metrics["sentiment_distribution"].get(sentiment, 0) + 1
            )

            # Update category distribution
            category = data.get("category", "general")
            if category not in metrics.get("category_distribution", {}):
                metrics["category_distribution"] = metrics.get(
                    "category_distribution", {}
                )
            metrics["category_distribution"][category] = (
                metrics["category_distribution"].get(category, 0) + 1
            )

            # Update daily stats
            today = datetime.utcnow().strftime("%Y-%m-%d")
            if "daily_stats" not in metrics:
                metrics["daily_stats"] = {}
            if today not in metrics["daily_stats"]:
                metrics["daily_stats"][today] = 0
            metrics["daily_stats"][today] += 1

            # Update timestamp
            metrics["last_updated"] = datetime.utcnow().isoformat()

            # Save updated metrics
            await self._save_json(self.metrics_path, metrics)

            logger.info(
                f"Metrics updated | "
                f"Total: {metrics['total_requests']} | "
                f"Sentiment: {sentiment} | "
                f"Category: {category}"
            )

        except Exception as e:
            logger.exception(f"Failed to update metrics: {str(e)}")

    async def _load_json(self, path: str) -> dict:
        """Load JSON file"""
        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load JSON from {path}: {str(e)}")
            return {}

    async def _save_json(self, path: str, data: dict):
        """Save JSON file"""
        async with aiofiles.open(path, "w") as f:
            content = json.dumps(data, indent=2, ensure_ascii=False)
            await f.write(content)
            logger.debug(f"Saved JSON to {path}")
