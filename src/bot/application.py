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
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from src.db.database import Database
from src.cache.redis import RedisClient
from src.bot.handlers.start import start_handler
from src.bot.handlers.help import help_handler
from src.bot.handlers.callbacks import callback_handler


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

        # Core command handlers
        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("help", help_handler))

        # Callback query handler for inline keyboard buttons
        self.app.add_handler(CallbackQueryHandler(callback_handler))

        # Message handler for Twitter URLs
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.Regex(r"(https?://)?(twitter\.com|x\.com)/\w+"),
                self._handle_twitter_url,
            )
        )

        # Message handler for general text input flows (e.g., username input after button press)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._handle_text_input,
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

    async def _handle_text_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle general text input (for flows after button presses)."""
        text = update.message.text.strip()
        logger.info(f"Received text input: {text}")

        # TODO: Wire up context-based flow handling
        # For now, just acknowledge
        await update.message.reply_text(
            f"📝 收到输入: {text}\n\n请使用命令或按钮操作。"
        )

    def run(self) -> None:
        """Run the bot using run_polling which handles everything correctly."""
        import asyncio

        async def init_services():
            """Initialize db and redis."""
            await self.db.init()
            await self.redis.init()
            logger.info("Services initialized")

        # Initialize services in their own event loop
        asyncio.run(init_services())

        # Build application
        self.app = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # run_polling creates its own event loop and properly handles
        # startup/shutdown/polling
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
