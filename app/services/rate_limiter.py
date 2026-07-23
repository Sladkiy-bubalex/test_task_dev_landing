import json
import time
import aiofiles
from typing import Tuple
from loguru import logger
from app.config import settings


class RateLimiter:
    def __init__(self):
        self.window = settings.RATE_LIMIT_WINDOW
        self.max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        self.storage_path = f"{settings.DATA_DIR}/rate_limits.json"

        logger.info(
            f"Rate limiter initialized: {self.max_requests} requests per {self.window}s"
        )
        logger.debug(f"Rate limit storage: {self.storage_path}")

    async def check_rate_limit(self, client_id: str) -> Tuple[bool, dict]:
        """Check if the client has exceeded the rate limit"""
        logger.debug(f"Checking rate limit for client: {client_id}")

        try:
            limits = await self._load_limits()
            current_time = time.time()

            # Log current state
            logger.debug(f"Current limits state: {len(limits)} entries")

            # Clean up old entries
            old_count = len(limits)
            limits = {
                k: v
                for k, v in limits.items()
                if current_time - v["window_start"] < self.window
            }
            cleaned_count = old_count - len(limits)
            if cleaned_count > 0:
                logger.debug(f"Cleaned {cleaned_count} expired rate limit entries")

            # Check client's limit
            if client_id in limits:
                client_data = limits[client_id]

                if current_time - client_data["window_start"] < self.window:
                    if client_data["count"] >= self.max_requests:
                        remaining_time = int(
                            self.window - (current_time - client_data["window_start"])
                        )
                        logger.warning(
                            f"Rate limit exceeded for {client_id} | "
                            f"Count: {client_data['count']}/{self.max_requests} | "
                            f"Reset in: {remaining_time}s"
                        )

                        return False, {
                            "error": "Rate limit exceeded",
                            "retry_after": remaining_time,
                        }

                    client_data["count"] += 1
                    logger.debug(
                        f"Rate limit incremented for {client_id}: "
                        f"{client_data['count']}/{self.max_requests}"
                    )
                else:
                    # Reset window
                    limits[client_id] = {"window_start": current_time, "count": 1}
                    logger.debug(f"Rate limit window reset for {client_id}")
            else:
                limits[client_id] = {"window_start": current_time, "count": 1}
                logger.debug(f"New rate limit entry created for {client_id}")

            # Save updated limits
            await self._save_limits(limits)

            remaining = self.max_requests - limits[client_id]["count"]
            logger.info(
                f"Rate limit check passed for {client_id} | "
                f"Remaining: {remaining}/{self.max_requests}"
            )

            return True, {
                "remaining": remaining,
                "limit": self.max_requests,
                "window": self.window,
            }

        except Exception as e:
            logger.exception(f"Rate limit check failed: {str(e)}")
            logger.warning("Allowing request due to rate limiter failure")
            # If rate limiting fails, allow the request
            return True, {"error": "Rate limiting unavailable"}

    async def _load_limits(self) -> dict:
        try:
            async with aiofiles.open(self.storage_path, "r") as f:
                content = await f.read()
                limits = json.loads(content)
                logger.debug(f"Loaded {len(limits)} rate limit entries from storage")
                return limits
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.debug(f"No existing rate limits found: {str(e)}")
            return {}

    async def _save_limits(self, limits: dict):
        async with aiofiles.open(self.storage_path, "w") as f:
            content = json.dumps(limits, indent=2)
            await f.write(content)
            logger.debug(f"Saved {len(limits)} rate limit entries to storage")
