"""Channel service for managing Telegram channels and groups."""

import logging
from typing import Dict, Optional

from telegram import Bot
from telegram.error import TelegramError
from telegram.constants import ChatType


logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing private channels and discussion groups."""

    def __init__(self, bot: Bot):
        """Initialize service."""
        self.bot = bot

    async def create_private_channel(self, user_id: int, username: str) -> str:
        """Create a private channel for user's backups.

        Returns the channel ID.
        """
        try:
            # Create private channel
            chat = await self.bot.create_channel(
                title=f"📦 Twitter Backup - {username}",
                description=f"用于存放 {username} 的推特备份数据",
                is_private=True,
            )
            channel_id = str(chat.id)
            logger.info(f"Created private channel {channel_id} for user {user_id}")
            return channel_id

        except TelegramError as e:
            logger.error(f"Failed to create channel for user {user_id}: {e}")
            raise

    async def create_discussion_group(self, user_id: int, username: str) -> str:
        """Create a discussion group for commands.

        Returns the group ID.
        """
        try:
            # Create group
            chat = await self.bot.create_group(
                title=f"🤖 @{username} - Backup Bot",
                description="用于与 Twitter 备份机器人交互",
            )
            group_id = str(chat.id)
            logger.info(f"Created discussion group {group_id} for user {user_id}")
            return group_id

        except TelegramError as e:
            logger.error(f"Failed to create group for user {user_id}: {e}")
            raise

    async def create_user_channels(self, user_id: int, username: str) -> Dict[str, str]:
        """Create both private channel and discussion group for a user.

        Returns dict with channel_id and discussion_group_id.
        """
        try:
            # Create discussion group first
            group = await self.create_discussion_group(user_id, username)

            # Create private channel
            channel = await self.create_private_channel(user_id, username)

            # Link channel to group (if supported)
            try:
                await self.bot.link_chat(channel_id=channel, discussion_group_id=group)
            except TelegramError:
                # Linking might not be supported, continue anyway
                pass

            return {
                "private_channel_id": channel,
                "discussion_group_id": group,
            }

        except TelegramError as e:
            logger.error(f"Failed to create channels for user {user_id}: {e}")
            raise

    async def invite_bot_to_channel(self, channel_id: str) -> bool:
        """Invite bot to a channel."""
        try:
            chat = await self.bot.get_chat(channel_id)
            # Bot needs to be added as admin manually in most cases
            logger.info(f"Channel {channel_id}: {chat.title}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to get channel {channel_id}: {e}")
            return False

    async def get_channel_invite_link(self, channel_id: str) -> Optional[str]:
        """Get invite link for a channel."""
        try:
            chat = await self.bot.get_chat(channel_id)
            if hasattr(chat, "invite_link") and chat.invite_link:
                return chat.invite_link

            # Generate new link
            link = await self.bot.create_chat_invite_link(
                channel_id,
                name="Twitter Backup Bot Invite",
            )
            return link.invite_link
        except TelegramError as e:
            logger.error(f"Failed to get invite link for {channel_id}: {e}")
            return None

    async def send_to_channel(
        self,
        channel_id: str,
        text: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send message to user's private channel."""
        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=parse_mode,
                disable_notification=True,
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send to channel {channel_id}: {e}")
            return False

    async def send_media_to_channel(
        self,
        channel_id: str,
        media_type: str,
        file_path: str,
        caption: Optional[str] = None,
    ) -> bool:
        """Send media to user's private channel."""
        try:
            with open(file_path, "rb") as f:
                if media_type == "photo":
                    await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=f,
                        caption=caption,
                        disable_notification=True,
                    )
                elif media_type == "video":
                    await self.bot.send_video(
                        chat_id=channel_id,
                        video=f,
                        caption=caption,
                        disable_notification=True,
                    )
                else:
                    await self.bot.send_document(
                        chat_id=channel_id,
                        document=f,
                        caption=caption,
                        disable_notification=True,
                    )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send media to {channel_id}: {e}")
            return False
