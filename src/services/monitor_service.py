"""Monitor service for tweet monitoring and backup."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Bot

from src.db.database import Database
from src.db.repositories import (
    UserRepository,
    TwitterAccountRepository,
    TweetRepository,
    TweetMediaRepository,
    MonitorStatsRepository,
)
from src.twitter.client import TwitterClient, get_twitter_client
from src.twitter.parser import TweetParser
from src.media.downloader import MediaDownloader
from src.media.uploader import MediaUploader
from src.services.channel_service import ChannelService
from src.scheduler.adaptive import AdaptiveScheduler


logger = logging.getLogger(__name__)


class MonitorService:
    """Service for monitoring tweets and performing backups."""

    def __init__(
        self,
        db: Database,
        bot: Bot,
        twitter_client: TwitterClient,
    ):
        """Initialize service."""
        self.db = db
        self.bot = bot
        self.twitter_client = twitter_client

        self.user_repo = UserRepository(db)
        self.account_repo = TwitterAccountRepository(db)
        self.tweet_repo = TweetRepository(db)
        self.media_repo = TweetMediaRepository(db)
        self.stats_repo = MonitorStatsRepository(db)

        self.channel_service = ChannelService(bot)
        self.parser = TweetParser()
        self.media_downloader = MediaDownloader()
        self.media_uploader = MediaUploader(bot)
        self.scheduler = AdaptiveScheduler(db, None)  # Will be set later

    def set_scheduler(self, scheduler: AdaptiveScheduler) -> None:
        """Set the scheduler."""
        self.scheduler = scheduler

    async def fetch_and_backup_tweets(
        self,
        account_id: int,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> Dict:
        """Fetch and backup tweets for an account."""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            return {"success": False, "error": "Account not found"}

        user = await self.user_repo.get_by_id(account.user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Fetch tweets from Twitter
        tweets = await self.twitter_client.get_user_tweets(
            account.twitter_username,
            limit=limit,
            since=since,
        )

        if not tweets:
            return {
                "success": True,
                "message": "没有新推文",
                "count": 0,
            }

        saved_count = 0
        media_count = 0

        for tweet_data in tweets:
            # Check if already saved
            existing = await self.tweet_repo.get_by_tweet_id(tweet_data["id"])
            if existing:
                continue

            # Save tweet
            tweet = await self.tweet_repo.create(
                account_id=account_id,
                tweet_id=tweet_data["id"],
                author_username=tweet_data["author_username"],
                content=tweet_data["text"],
                author_display_name=tweet_data.get("author_display_name"),
                is_thread=tweet_data.get("is_thread", False),
                reply_to_tweet_id=tweet_data.get("reply_to_tweet_id"),
                posted_at=(
                    datetime.fromisoformat(tweet_data["posted_at"])
                    if tweet_data.get("posted_at")
                    else None
                ),
            )

            saved_count += 1

            # Download and upload media
            if tweet_data.get("media") and user.private_channel_id:
                for media_item in tweet_data["media"]:
                    try:
                        # Download media
                        media_path = await self.media_downloader.download_media(
                            media_item["url"], media_item["type"]
                        )

                        if media_path and media_path.get("filename"):
                            # Upload to Telegram
                            file_id = await self.media_uploader.upload_video(
                                file_path=media_path["filename"],
                                chat_id=int(user.private_channel_id),
                                caption=f"📎 @{account.twitter_username}: {tweet_data['text'][:100]}...",
                            )

                            # Save media record
                            if file_id:
                                await self.media_repo.create(
                                    tweet_id=tweet.id,
                                    media_type=media_item["type"],
                                    media_url=media_item["url"],
                                    telegram_file_id=file_id,
                                    local_path=media_path["filename"],
                                )
                                media_count += 1

                            # Cleanup local file
                            self.media_downloader.cleanup_file(media_path["filename"])
                    except Exception as e:
                        logger.error(f"Failed to process media: {e}")

        # Update stats
        if self.scheduler:
            await self.scheduler.update_stats(account_id, saved_count)

        return {
            "success": True,
            "message": f"备份完成: {saved_count} 条推文, {media_count} 个媒体",
            "count": saved_count,
            "media_count": media_count,
        }

    async def backup_history(
        self,
        account_id: int,
        days: Optional[int] = None,
    ) -> Dict:
        """Backup historical tweets for an account.

        Args:
            account_id: Twitter account ID
            days: Number of days to look back (None = all)
        """
        since = None
        if days:
            since = datetime.utcnow() - timedelta(days=days)

        return await self.fetch_and_backup_tweets(
            account_id=account_id,
            since=since,
            limit=3200,  # Twitter's limit
        )

    async def monitor_account(self, account_id: int) -> Dict:
        """Monitor an account for new tweets (called by scheduler)."""
        return await self.fetch_and_backup_tweets(account_id)

    async def get_backup_status(self, account_id: int) -> Dict:
        """Get backup status for an account."""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            return {"error": "Account not found"}

        tweet_count = await self.tweet_repo.get_count_by_account(account_id)
        recent_stats = await self.stats_repo.get_recent_stats(account_id)

        next_check = None
        if self.scheduler:
            next_check = await self.scheduler.get_next_check_time(account_id)

        return {
            "username": account.twitter_username,
            "display_name": account.display_name,
            "is_active": account.is_active,
            "last_checked_at": (
                account.last_checked_at.isoformat() if account.last_checked_at else None
            ),
            "tweet_count": tweet_count,
            "recent_posts": recent_stats.posts_count if recent_stats else 0,
            "computed_interval": (
                recent_stats.computed_interval_seconds if recent_stats else None
            ),
            "next_check": next_check.isoformat() if next_check else None,
        }
