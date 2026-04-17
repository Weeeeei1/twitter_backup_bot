"""Bot application setup and handlers."""

import asyncio
import logging
import signal
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.config import settings
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

    async def initialize_and_run(self) -> None:
        """Initialize and run the bot with proper event loop handling."""
        # Build application in async context
        self.app = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # Initialize the app (creates bot instance, sets up update queue)
        await self.app.initialize()
        logger.info("Bot initialized")

        # Start the app
        await self.app.start()
        logger.info("Bot started, waiting for updates...")

        # Create an event to keep the bot running
        # This allows proper shutdown via signals
        stop_event = asyncio.Event()

        def handle_signal(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            stop_event.set()

        # Register signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Wait for shutdown signal
        await stop_event.wait()

        logger.info("Shutdown signal received")

    async def shutdown(self) -> None:
        """Shutdown the bot gracefully."""
        if self.app:
            logger.info("Shutting down bot...")
            try:
                await self.app.stop()
                await self.app.shutdown()
                logger.info("Bot shutdown complete")
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")
