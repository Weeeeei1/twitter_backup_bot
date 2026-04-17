"""Bot application setup and handlers."""

import asyncio
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.db.database import Database
from src.cache.redis import RedisClient
from src.bot.handlers.start import start_handler
from src.bot.handlers.help import help_handler
from src.bot.handlers.add_account import add_account_handler
from src.bot.handlers.list_accounts import list_accounts_handler
from src.bot.handlers.remove_account import remove_account_handler
from src.bot.handlers.status import status_handler
from src.bot.handlers.backup import backup_handler
from src.bot.handlers.history import history_handler


logger = logging.getLogger(__name__)


class BotApplication:
    """Telegram bot application."""

    def __init__(self, bot_token: str, db: Database, redis: RedisClient):
        """Initialize bot application."""
        self.bot_token = bot_token
        self.db = db
        self.redis = redis
        self.app: Optional[Application] = None

    def _register_handlers(self) -> None:
        """Register command handlers."""
        if self.app is None:
            return

        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("help", help_handler))
        self.app.add_handler(CommandHandler("add_account", add_account_handler))
        self.app.add_handler(CommandHandler("list_accounts", list_accounts_handler))
        self.app.add_handler(CommandHandler("remove_account", remove_account_handler))
        self.app.add_handler(CommandHandler("status", status_handler))
        self.app.add_handler(CommandHandler("backup", backup_handler))
        self.app.add_handler(CommandHandler("history", history_handler))

        # Message handler for Twitter URLs
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.Regex(r"(https?://)?(twitter\.com|x\.com)/\w+"),
                self._handle_twitter_url,
            )
        )

    async def _handle_twitter_url(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle Twitter URL messages."""
        url = update.message.text.strip()
        logger.info(f"Received Twitter URL: {url}")

        await update.message.reply_text(
            f"📋 Received URL: {url}\n\nUse /backup to back up this account's tweets."
        )

    def run(self) -> None:
        """Run the bot - using asyncio.run() to properly manage event loop."""
        # Build application
        self.app = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # Use asyncio.run() to properly manage the event loop
        # This avoids the "event loop closed" issue
        import asyncio

        async def init_and_poll():
            # Initialize services
            await self.db.init()
            await self.redis.init()
            logger.info("Services initialized")

            # Start polling
            await self.app.initialize()
            await self.app.start()
            logger.info("Bot started, waiting for updates...")

            # Run until interrupted
            try:
                await self.app.idle()
            except Exception as e:
                logger.error(f"Error during idle: {e}")

        asyncio.run(init_and_poll())
