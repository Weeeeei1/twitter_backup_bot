"""Rate limiter for Twitter API."""

import asyncio
import logging
import time
from typing import Dict, Optional

from src.cache.redis import RedisClient


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Twitter API requests."""

    def __init__(
        self,
        redis: RedisClient,
        default_limit: int = 60,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter."""
        self.redis = redis
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._local_counts: Dict[str, int] = {}
        self._last_reset: Dict[str, float] = {}

    async def is_allowed(self, key: str, limit: Optional[int] = None) -> bool:
        """Check if request is allowed under rate limit."""
        limit = limit or self.default_limit

        # Check Redis-based rate limit first
        allowed = await self.redis.check_rate_limit(
            key, limit=limit, window=self.window_seconds
        )

        if not allowed:
            logger.warning(f"Rate limited: {key}")
            return False

        # Local check as backup
        current_time = time.time()
        if key not in self._last_reset:
            self._last_reset[key] = current_time
            self._local_counts[key] = 0

        # Reset window if expired
        if current_time - self._last_reset[key] >= self.window_seconds:
            self._last_reset[key] = current_time
            self._local_counts[key] = 0

        # Increment local counter
        self._local_counts[key] += 1

        if self._local_counts[key] > limit:
            logger.warning(f"Local rate limit exceeded: {key}")
            return False

        return True

    async def wait_if_needed(self, key: str, limit: Optional[int] = None) -> None:
        """Wait if rate limited."""
        limit = limit or self.default_limit

        while not await self.is_allowed(key, limit):
            await asyncio.sleep(1)

    async def get_remaining(self, key: str, limit: Optional[int] = None) -> int:
        """Get remaining requests in current window."""
        limit = limit or self.default_limit

        current_time = time.time()
        if key not in self._last_reset:
            return limit

        if current_time - self._last_reset[key] >= self.window_seconds:
            return limit

        used = self._local_counts.get(key, 0)
        return max(0, limit - used)


class TwitterRateLimiter(RateLimiter):
    """Rate limiter specific to Twitter API."""

    # Twitter's rate limit categories
    RATE_LIMITS = {
        "user_tweets": {"limit": 100, "window": 900},  # per 15 minutes
        "search": {"limit": 180, "window": 900},
        "timeline": {"limit": 100, "window": 900},
        "lookup": {"limit": 300, "window": 900},
    }

    def __init__(self, redis: RedisClient):
        """Initialize Twitter rate limiter."""
        super().__init__(redis, default_limit=60, window_seconds=60)
        self.rate_limits = self.RATE_LIMITS

    async def is_user_tweets_allowed(self) -> bool:
        """Check if user tweets request is allowed."""
        return await self.is_allowed(
            "twitter:user_tweets", self.rate_limits["user_tweets"]["limit"]
        )

    async def is_search_allowed(self) -> bool:
        """Check if search request is allowed."""
        return await self.is_allowed(
            "twitter:search", self.rate_limits["search"]["limit"]
        )

    async def wait_for_user_tweets(self) -> None:
        """Wait if user tweets request is rate limited."""
        await self.wait_if_needed(
            "twitter:user_tweets", self.rate_limits["user_tweets"]["limit"]
        )

    async def wait_for_search(self) -> None:
        """Wait if search request is rate limited."""
        await self.wait_if_needed("twitter:search", self.rate_limits["search"]["limit"])
