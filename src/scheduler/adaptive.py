"""Adaptive polling interval algorithm."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.config import settings
from src.cache.redis import RedisClient
from src.db.database import Database
from src.db.repositories import MonitorStatsRepository, TwitterAccountRepository


logger = logging.getLogger(__name__)


class AdaptiveScheduler:
    """Adaptive polling scheduler that adjusts check intervals based on activity."""

    def __init__(
        self,
        db: Database,
        redis: RedisClient,
        base_interval: Optional[int] = None,
        min_interval: Optional[int] = None,
        max_interval: Optional[int] = None,
    ):
        """Initialize scheduler."""
        self.db = db
        self.redis = redis

        # Interval settings
        self.base_interval = (
            base_interval or settings.base_check_interval
        )  # 300s default
        self.min_interval = min_interval or settings.min_check_interval  # 60s default
        self.max_interval = max_interval or settings.max_check_interval  # 3600s default

        # Sliding window for stats
        self.window_minutes = 30  # Analyze last 30 minutes

        # Cache for computed intervals
        self._interval_cache: Dict[int, int] = {}

    async def compute_interval(self, account_id: int) -> int:
        """Compute adaptive polling interval for an account.

        Algorithm:
        - If no recent activity, use base interval
        - If posts are frequent, decrease interval
        - If posts are rare, increase interval
        """
        # Check cache first
        if account_id in self._interval_cache:
            cached_interval = await self.redis.get_account_interval(account_id)
            if cached_interval:
                return cached_interval

        # Get recent stats from database
        stats_repo = MonitorStatsRepository(self.db)
        recent_stats = await stats_repo.get_recent_stats(
            account_id, self.window_minutes
        )

        if not recent_stats:
            # No recent data, use base interval
            interval = self.base_interval
        else:
            # Calculate interval based on posting frequency
            posts_count = recent_stats.posts_count
            window_duration = (
                (recent_stats.window_end - recent_stats.window_start).total_seconds()
                if recent_stats.window_end and recent_stats.window_start
                else 0
            )

            if posts_count == 0:
                # No posts in window, increase interval
                interval = min(self.base_interval * 2, self.max_interval)
            else:
                # Calculate average interval between posts
                avg_post_interval = (
                    window_duration / posts_count
                    if posts_count > 0
                    else self.base_interval
                )

                # Compute new interval
                # Higher posting frequency = shorter interval
                # Formula: base_interval * (avg_post_interval / target_interval)
                # target_interval is what we consider "normal" (base_interval)
                ratio = avg_post_interval / self.base_interval
                ratio = max(0.1, min(10.0, ratio))  # Clamp ratio

                interval = int(self.base_interval * ratio)

        # Clamp to min/max bounds
        interval = max(self.min_interval, min(self.max_interval, interval))

        # Update cache
        self._interval_cache[account_id] = interval
        await self.redis.set_account_interval(account_id, interval)

        logger.debug(f"Computed interval for account {account_id}: {interval}s")
        return interval

    async def update_stats(
        self,
        account_id: int,
        posts_found: int,
    ) -> None:
        """Update monitoring statistics for an account."""
        stats_repo = MonitorStatsRepository(self.db)

        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)

        # Calculate average interval
        avg_interval = None
        computed_interval = None

        if posts_found > 0:
            window_duration = self.window_minutes * 60
            avg_interval = window_duration / posts_found
            computed_interval = await self.compute_interval(account_id)

        await stats_repo.create(
            account_id=account_id,
            window_start=window_start,
            window_end=now,
            posts_count=posts_found,
            avg_interval_seconds=avg_interval,
            computed_interval_seconds=computed_interval,
        )

        # Update last checked
        account_repo = TwitterAccountRepository(self.db)
        await account_repo.update_last_checked(account_id, now)

    async def get_next_check_time(self, account_id: int) -> datetime:
        """Get the next scheduled check time for an account."""
        interval = await self.compute_interval(account_id)
        return datetime.utcnow() + timedelta(seconds=interval)

    def clear_cache(self, account_id: Optional[int] = None) -> None:
        """Clear interval cache."""
        if account_id:
            self._interval_cache.pop(account_id, None)
        else:
            self._interval_cache.clear()
