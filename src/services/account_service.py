"""Account service for managing Twitter accounts."""

import logging
from typing import List, Optional

from telegram import Bot
from telegram.error import TelegramError

from src.db.database import Database
from src.db.repositories import (
    UserRepository,
    TwitterAccountRepository,
    UserSettingsRepository,
)
from src.services.channel_service import ChannelService


logger = logging.getLogger(__name__)


class AccountService:
    """Service for managing user Twitter accounts."""

    def __init__(self, db: Database, bot: Bot):
        """Initialize service."""
        self.db = db
        self.bot = bot
        self.user_repo = UserRepository(db)
        self.account_repo = TwitterAccountRepository(db)
        self.settings_repo = UserSettingsRepository(db)
        self.channel_service = ChannelService(bot)

    async def get_or_create_user(
        self, telegram_id: int, username: Optional[str] = None
    ) -> dict:
        """Get or create user and ensure channels exist."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)

        if not user:
            # Create user
            user = await self.user_repo.create(
                telegram_id=telegram_id,
                username=username,
            )
            logger.info(f"Created new user {telegram_id}")

        # Ensure channels exist
        if not user.private_channel_id or not user.discussion_group_id:
            try:
                channels = await self.channel_service.create_user_channels(
                    user_id=telegram_id,
                    username=username or f"user_{telegram_id}",
                )
                await self.user_repo.update_channel_ids(
                    telegram_id=telegram_id,
                    private_channel_id=channels["private_channel_id"],
                    discussion_group_id=channels["discussion_group_id"],
                )
                user = await self.user_repo.get_by_telegram_id(telegram_id)
            except TelegramError as e:
                logger.error(f"Failed to create channels for user {telegram_id}: {e}")

        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "private_channel_id": user.private_channel_id,
            "discussion_group_id": user.discussion_group_id,
        }

    async def add_account(
        self,
        telegram_id: int,
        twitter_username: str,
    ) -> dict:
        """Add a Twitter account to monitor."""
        # Ensure user exists
        user_data = await self.get_or_create_user(telegram_id)
        user = await self.user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise ValueError("User not found")

        # Check if account already exists
        existing = await self.account_repo.get_by_user_and_username(
            user.id, twitter_username
        )
        if existing:
            return {
                "success": False,
                "error": f"@{twitter_username} 已经添加过了",
                "account": {
                    "id": existing.id,
                    "username": existing.twitter_username,
                },
            }

        # Create new account
        account = await self.account_repo.create(
            user_id=user.id,
            twitter_username=twitter_username,
        )

        logger.info(f"Added Twitter account @{twitter_username} for user {telegram_id}")

        return {
            "success": True,
            "account": {
                "id": account.id,
                "username": account.twitter_username,
                "display_name": account.display_name,
            },
        }

    async def remove_account(
        self,
        telegram_id: int,
        twitter_username: str,
    ) -> dict:
        """Remove a Twitter account from monitoring."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return {"success": False, "error": "用户不存在"}

        account = await self.account_repo.get_by_user_and_username(
            user.id, twitter_username
        )
        if not account:
            return {"success": False, "error": f"@{twitter_username} 不在监控列表中"}

        await self.account_repo.delete(account.id)

        logger.info(
            f"Removed Twitter account @{twitter_username} for user {telegram_id}"
        )

        return {"success": True, "username": twitter_username}

    async def list_accounts(self, telegram_id: int) -> List[dict]:
        """List all monitored accounts for a user."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return []

        accounts = await self.account_repo.get_all_by_user(user.id)

        return [
            {
                "id": acc.id,
                "username": acc.twitter_username,
                "display_name": acc.display_name,
                "is_active": acc.is_active,
                "added_at": acc.added_at.isoformat() if acc.added_at else None,
                "last_checked_at": (
                    acc.last_checked_at.isoformat() if acc.last_checked_at else None
                ),
            }
            for acc in accounts
        ]

    async def get_account_stats(self, telegram_id: int) -> dict:
        """Get statistics for user's monitored accounts."""
        accounts = await self.list_accounts(telegram_id)

        total_accounts = len(accounts)
        active_accounts = sum(1 for acc in accounts if acc["is_active"])

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "accounts": accounts,
        }
