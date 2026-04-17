"""Data repositories for database access."""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import Database
from src.db.models import (
    User,
    TwitterAccount,
    Tweet,
    TweetMedia,
    MonitorStats,
    UserSettings,
)


logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        private_channel_id: Optional[str] = None,
        discussion_group_id: Optional[str] = None,
    ) -> User:
        """Create new user."""
        async with self.db.session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                private_channel_id=private_channel_id,
                discussion_group_id=discussion_group_id,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    async def update_channel_ids(
        self,
        telegram_id: int,
        private_channel_id: Optional[str] = None,
        discussion_group_id: Optional[str] = None,
    ) -> Optional[User]:
        """Update user's channel IDs."""
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                if private_channel_id:
                    user.private_channel_id = private_channel_id
                if discussion_group_id:
                    user.discussion_group_id = discussion_group_id
                user.updated_at = datetime.utcnow()
            return user


class TwitterAccountRepository:
    """Repository for TwitterAccount model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def get_by_id(self, account_id: int) -> Optional[TwitterAccount]:
        """Get account by ID."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount).where(TwitterAccount.id == account_id)
            )
            return result.scalar_one_or_none()

    async def get_by_user_and_username(
        self, user_id: int, twitter_username: str
    ) -> Optional[TwitterAccount]:
        """Get account by user ID and Twitter username."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount).where(
                    and_(
                        TwitterAccount.user_id == user_id,
                        TwitterAccount.twitter_username == twitter_username.lower(),
                    )
                )
            )
            return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> List[TwitterAccount]:
        """Get all accounts for a user."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount)
                .where(TwitterAccount.user_id == user_id)
                .order_by(TwitterAccount.added_at.desc())
            )
            return list(result.scalars().all())

    async def get_active_accounts(self) -> List[TwitterAccount]:
        """Get all active accounts."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount).where(TwitterAccount.is_active == True)
            )
            return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        twitter_username: str,
        twitter_user_id: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> TwitterAccount:
        """Create new Twitter account."""
        async with self.db.session() as session:
            account = TwitterAccount(
                user_id=user_id,
                twitter_username=twitter_username.lower(),
                twitter_user_id=twitter_user_id,
                display_name=display_name,
            )
            session.add(account)
            await session.flush()
            await session.refresh(account)
            return account

    async def update_last_checked(
        self, account_id: int, last_checked_at: datetime
    ) -> None:
        """Update last checked timestamp."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount).where(TwitterAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            if account:
                account.last_checked_at = last_checked_at

    async def delete(self, account_id: int) -> bool:
        """Delete account."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TwitterAccount).where(TwitterAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            if account:
                await session.delete(account)
                return True
            return False


class TweetRepository:
    """Repository for Tweet model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def get_by_tweet_id(self, tweet_id: str) -> Optional[Tweet]:
        """Get tweet by Twitter ID."""
        async with self.db.session() as session:
            result = await session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet_id)
            )
            return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: int,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Tweet]:
        """Get tweets for account."""
        async with self.db.session() as session:
            query = select(Tweet).where(Tweet.account_id == account_id)
            if since:
                query = query.where(Tweet.posted_at >= since)
            query = query.order_by(Tweet.posted_at.desc()).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_count_by_account(self, account_id: int) -> int:
        """Get tweet count for account."""
        async with self.db.session() as session:
            result = await session.execute(
                select(func.count(Tweet.id)).where(Tweet.account_id == account_id)
            )
            return result.scalar() or 0

    async def create(
        self,
        account_id: int,
        tweet_id: str,
        author_username: str,
        content: Optional[str] = None,
        author_display_name: Optional[str] = None,
        is_thread: bool = False,
        reply_to_tweet_id: Optional[str] = None,
        reply_to_username: Optional[str] = None,
        posted_at: Optional[datetime] = None,
    ) -> Tweet:
        """Create new tweet."""
        async with self.db.session() as session:
            tweet = Tweet(
                account_id=account_id,
                tweet_id=tweet_id,
                author_username=author_username,
                content=content,
                author_display_name=author_display_name,
                is_thread=is_thread,
                reply_to_tweet_id=reply_to_tweet_id,
                reply_to_username=reply_to_username,
                posted_at=posted_at,
            )
            session.add(tweet)
            await session.flush()
            await session.refresh(tweet)
            return tweet

    async def mark_deleted(self, tweet_id: str) -> None:
        """Mark tweet as deleted."""
        async with self.db.session() as session:
            result = await session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet_id)
            )
            tweet = result.scalar_one_or_none()
            if tweet:
                tweet.is_deleted = True


class TweetMediaRepository:
    """Repository for TweetMedia model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def create(
        self,
        tweet_id: int,
        media_type: str,
        media_url: str,
        telegram_file_id: Optional[str] = None,
        local_path: Optional[str] = None,
    ) -> TweetMedia:
        """Create new media record."""
        async with self.db.session() as session:
            media = TweetMedia(
                tweet_id=tweet_id,
                media_type=media_type,
                media_url=media_url,
                telegram_file_id=telegram_file_id,
                local_path=local_path,
            )
            session.add(media)
            await session.flush()
            await session.refresh(media)
            return media

    async def update_telegram_file_id(
        self, media_id: int, telegram_file_id: str
    ) -> None:
        """Update Telegram file ID after upload."""
        async with self.db.session() as session:
            result = await session.execute(
                select(TweetMedia).where(TweetMedia.id == media_id)
            )
            media = result.scalar_one_or_none()
            if media:
                media.telegram_file_id = telegram_file_id
                media.uploaded_at = datetime.utcnow()


class MonitorStatsRepository:
    """Repository for MonitorStats model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def get_recent_stats(
        self, account_id: int, window_minutes: int = 30
    ) -> Optional[MonitorStats]:
        """Get recent monitoring stats."""
        async with self.db.session() as session:
            since = datetime.utcnow().replace(second=0, microsecond=0)
            result = await session.execute(
                select(MonitorStats)
                .where(
                    and_(
                        MonitorStats.account_id == account_id,
                        MonitorStats.window_end >= since,
                    )
                )
                .order_by(MonitorStats.window_end.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def create(
        self,
        account_id: int,
        window_start: datetime,
        window_end: datetime,
        posts_count: int = 0,
        avg_interval_seconds: Optional[float] = None,
        computed_interval_seconds: Optional[float] = None,
    ) -> MonitorStats:
        """Create new stats record."""
        async with self.db.session() as session:
            stats = MonitorStats(
                account_id=account_id,
                window_start=window_start,
                window_end=window_end,
                posts_count=posts_count,
                avg_interval_seconds=avg_interval_seconds,
                computed_interval_seconds=computed_interval_seconds,
            )
            session.add(stats)
            await session.flush()
            await session.refresh(stats)
            return stats


class UserSettingsRepository:
    """Repository for UserSettings model."""

    def __init__(self, db: Database):
        """Initialize repository."""
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[UserSettings]:
        """Get settings by user ID."""
        async with self.db.session() as session:
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> UserSettings:
        """Get or create settings for user."""
        async with self.db.session() as session:
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()

            if not settings:
                settings = UserSettings(user_id=user_id)
                session.add(settings)
                await session.flush()
                await session.refresh(settings)

            return settings

    async def update(
        self,
        user_id: int,
        base_check_interval: Optional[int] = None,
        min_check_interval: Optional[int] = None,
        max_check_interval: Optional[int] = None,
        media_download_enabled: Optional[bool] = None,
        notifications_enabled: Optional[bool] = None,
    ) -> Optional[UserSettings]:
        """Update user settings."""
        async with self.db.session() as session:
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()
            if settings:
                if base_check_interval is not None:
                    settings.base_check_interval = base_check_interval
                if min_check_interval is not None:
                    settings.min_check_interval = min_check_interval
                if max_check_interval is not None:
                    settings.max_check_interval = max_check_interval
                if media_download_enabled is not None:
                    settings.media_download_enabled = media_download_enabled
                if notifications_enabled is not None:
                    settings.notifications_enabled = notifications_enabled
                settings.updated_at = datetime.utcnow()
            return settings
