"""Database models."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class User(Base):
    """Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    private_channel_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    discussion_group_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    twitter_accounts: Mapped[List["TwitterAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class TwitterAccount(Base):
    """Twitter account to monitor."""

    __tablename__ = "twitter_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    twitter_username: Mapped[str] = mapped_column(String(255), nullable=False)
    twitter_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="twitter_accounts")
    tweets: Mapped[List["Tweet"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    monitor_stats: Mapped[List["MonitorStats"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_twitter_accounts_user_username",
            "user_id",
            "twitter_username",
            unique=True,
        ),
    )


class Tweet(Base):
    """Collected tweet."""

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    tweet_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    author_username: Mapped[str] = mapped_column(String(255), nullable=False)
    author_display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_thread: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_to_tweet_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reply_to_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    account: Mapped["TwitterAccount"] = relationship(back_populates="tweets")
    media: Mapped[List["TweetMedia"]] = relationship(
        back_populates="tweet", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_tweets_account_posted", "account_id", "posted_at"),)


class TweetMedia(Base):
    """Tweet media attachment."""

    __tablename__ = "tweet_media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tweet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    media_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # photo, video, gif, poll
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    tweet: Mapped["Tweet"] = relationship(back_populates="media")


class MonitorStats(Base):
    """Monitoring statistics for adaptive interval calculation."""

    __tablename__ = "monitor_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_interval_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    computed_interval_seconds: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    account: Mapped["TwitterAccount"] = relationship(back_populates="monitor_stats")

    __table_args__ = (
        Index(
            "ix_monitor_stats_account_window",
            "account_id",
            "window_start",
            "window_end",
        ),
    )


class UserSettings(Base):
    """User settings."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    base_check_interval: Mapped[int] = mapped_column(Integer, default=300)
    min_check_interval: Mapped[int] = mapped_column(Integer, default=60)
    max_check_interval: Mapped[int] = mapped_column(Integer, default=3600)
    media_download_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="settings")
