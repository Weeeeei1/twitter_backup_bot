"""Redis client for caching and task queue."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis


logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper."""

    def __init__(self, redis_url: str):
        """Initialize Redis client."""
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def init(self) -> None:
        """Initialize Redis connection."""
        self.client = redis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )
        await self.client.ping()
        logger.info("Redis connection established")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    # Key prefixes
    PREFIX_ACCOUNT_LOCK = "lock:account:"
    PREFIX_INTERVAL = "interval:account:"
    PREFIX_QUEUE = "queue:tweets"
    PREFIX_RATE_LIMIT = "ratelimit:twitter:"

    async def set_with_ttl(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set key with TTL."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.setex(key, ttl, value)

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self.client.get(key)

    async def delete(self, key: str) -> None:
        """Delete key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0

    # Account polling lock
    async def acquire_account_lock(self, account_id: int, ttl: int = 60) -> bool:
        """Acquire lock for account polling."""
        key = f"{self.PREFIX_ACCOUNT_LOCK}{account_id}"
        return await self.client.set(key, "1", nx=True, ex=ttl)

    async def release_account_lock(self, account_id: int) -> None:
        """Release account polling lock."""
        key = f"{self.PREFIX_ACCOUNT_LOCK}{account_id}"
        await self.client.delete(key)

    # Adaptive interval cache
    async def set_account_interval(
        self, account_id: int, interval: int, ttl: int = 3600
    ) -> None:
        """Cache computed polling interval for account."""
        key = f"{self.PREFIX_INTERVAL}{account_id}"
        await self.client.setex(key, ttl, str(interval))

    async def get_account_interval(self, account_id: int) -> Optional[int]:
        """Get cached polling interval for account."""
        key = f"{self.PREFIX_INTERVAL}{account_id}"
        value = await self.client.get(key)
        return int(value) if value else None

    # Task queue
    async def enqueue_tweet_account(self, account_id: int) -> None:
        """Add account to tweet fetch queue."""
        await self.client.rpush(self.PREFIX_QUEUE, str(account_id))

    async def dequeue_tweet_account(self, timeout: int = 1) -> Optional[int]:
        """Get next account from tweet fetch queue."""
        result = await self.client.blpop(self.PREFIX_QUEUE, timeout=timeout)
        if result:
            return int(result[1])
        return None

    async def get_queue_length(self) -> int:
        """Get tweet queue length."""
        return await self.client.llen(self.PREFIX_QUEUE)

    # Rate limiting
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limited. Returns True if allowed, False if limited."""
        rate_key = f"{self.PREFIX_RATE_LIMIT}{key}"
        current = await self.client.get(rate_key)

        if current is None:
            await self.client.setex(rate_key, window, "1")
            return True

        if int(current) >= limit:
            return False

        await self.client.incr(rate_key)
        return True
