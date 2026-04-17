"""Scheduler pool for managing monitoring tasks."""

import asyncio
import logging
from typing import Dict, Set, Optional

from src.db.database import Database
from src.cache.redis import RedisClient
from src.scheduler.adaptive import AdaptiveScheduler


logger = logging.getLogger(__name__)


class SchedulerPool:
    """Pool of schedulers for accounts."""

    def __init__(
        self,
        db: Database,
        redis: RedisClient,
        num_workers: int = 3,
    ):
        """Initialize scheduler pool."""
        self.db = db
        self.redis = redis
        self.num_workers = num_workers

        # Adaptive schedulers per account
        self._schedulers: Dict[int, AdaptiveScheduler] = {}

        # Active tasks
        self._tasks: Set[asyncio.Task] = set()

        # Running flag
        self._running = False

        # Monitor service reference (set later)
        self.monitor_service = None

    def get_scheduler(self, account_id: int) -> AdaptiveScheduler:
        """Get or create scheduler for account."""
        if account_id not in self._schedulers:
            self._schedulers[account_id] = AdaptiveScheduler(self.db, self.redis)
        return self._schedulers[account_id]

    async def start(self) -> None:
        """Start the scheduler pool."""
        if self._running:
            return

        self._running = True
        logger.info(f"Starting scheduler pool with {self.num_workers} workers")

        # Start worker tasks
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def stop(self) -> None:
        """Stop the scheduler pool."""
        self._running = False
        logger.info("Stopping scheduler pool")

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("Scheduler pool stopped")

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine that processes accounts."""
        logger.debug(f"Worker {worker_id} started")

        while self._running:
            try:
                # Get next account from queue
                account_id = await self.redis.dequeue_tweet_account(timeout=1)

                if account_id is None:
                    continue

                # Check if account is already being processed
                lock_acquired = await self.redis.acquire_account_lock(account_id)
                if not lock_acquired:
                    # Re-queue if locked
                    await self.redis.enqueue_tweet_account(account_id)
                    continue

                try:
                    # Get scheduler for account
                    scheduler = self.get_scheduler(account_id)

                    # Compute interval
                    interval = await scheduler.compute_interval(account_id)

                    logger.info(
                        f"Worker {worker_id}: checking account {account_id}, next check in {interval}s"
                    )

                    # Sleep for interval
                    await asyncio.sleep(interval)

                    # Process account (fetch new tweets)
                    if self.monitor_service:
                        result = await self.monitor_service.monitor_account(account_id)
                        tweets_found = result.get("count", 0)
                        logger.info(
                            f"Worker {worker_id}: account {account_id} - found {tweets_found} tweets"
                        )
                    else:
                        tweets_found = 0
                        logger.warning(f"Worker {worker_id}: monitor_service not set")

                    # Update stats
                    await scheduler.update_stats(account_id, tweets_found)

                    # Re-queue for next check
                    await self.redis.enqueue_tweet_account(account_id)

                finally:
                    await self.redis.release_account_lock(account_id)

                # Small delay between accounts
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.debug(f"Worker {worker_id} stopped")

    async def enqueue_account(self, account_id: int) -> None:
        """Enqueue an account for monitoring."""
        await self.redis.enqueue_tweet_account(account_id)
        logger.debug(f"Enqueued account {account_id} for monitoring")

    async def get_queue_size(self) -> int:
        """Get current queue size."""
        return await self.redis.get_queue_length()
