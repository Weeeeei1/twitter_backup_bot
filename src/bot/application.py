"""Bot application setup and handlers."""

import asyncio
import logging
import re
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
from src.bot.menus.main_menu import main_menu
from src.bot.menus.account_menu import account_menu
from src.bot.menus.settings_menu import settings_menu
from src.bot import state as state_module
from src.services.account_service import AccountService


logger = logging.getLogger(__name__)


class BotApplication:
    """Telegram bot application."""

    def __init__(self, bot_token: str, db: Database, redis: RedisClient):
        """Initialize bot application."""
        self.bot_token = bot_token
        self.db = db
        self.redis = redis
        self.app: Optional[Application] = None
        self.account_service: Optional[AccountService] = None

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
        user = update.effective_user
        logger.info(
            f"Received text input: {text}, input_mode: {context.user_data.get('input_mode')}"
        )

        input_mode = context.user_data.get("input_mode")

        if input_mode == "add_account":
            # Validate username format
            if not re.match(r"^[A-Za-z0-9_]{1,15}$", text):
                await update.message.reply_text(
                    "❌ 用户名格式不正确\n\n请提供有效的 Twitter 用户名（不带@）",
                    reply_markup=account_menu(),
                )
                return

            # Use account service to add account
            try:
                result = await state_module.account_service.add_account(
                    telegram_id=user.id,
                    twitter_username=text,
                )
            except Exception as e:
                logger.error(f"Error adding account: {e}")
                context.user_data["input_mode"] = None
                await update.message.reply_text(
                    f"❌ 添加失败\n\n数据库错误，请重试。",
                    reply_markup=account_menu(),
                )
                return

            context.user_data["input_mode"] = None

            if result["success"]:
                await update.message.reply_text(
                    f"✅ **账号已添加**\n\n开始监控：@{text}\n\n新帖子会自动备份到您的私有频道。",
                    reply_markup=account_menu(),
                )
            else:
                await update.message.reply_text(
                    f"❌ 添加失败\n\n{result.get('error', '未知错误')}",
                    reply_markup=account_menu(),
                )

        elif input_mode == "remove_account":
            # Validate username format
            if not re.match(r"^[A-Za-z0-9_]{1,15}$", text):
                await update.message.reply_text(
                    "❌ 用户名格式不正确\n\n请提供有效的 Twitter 用户名（不带@）",
                    reply_markup=account_menu(),
                )
                return

            # Use account service to remove account
            result = await state_module.account_service.remove_account(
                telegram_id=user.id,
                twitter_username=text,
            )

            context.user_data["input_mode"] = None

            if result["success"]:
                await update.message.reply_text(
                    f"✅ **已移除**\n\n停止监控：@{text}",
                    reply_markup=account_menu(),
                )
            else:
                await update.message.reply_text(
                    f"❌ 移除失败\n\n{result.get('error', '未知错误')}",
                    reply_markup=account_menu(),
                )

        elif input_mode == "setchannel":
            # Validate channel ID format
            if not text.startswith("-100"):
                await update.message.reply_text(
                    "❌ 频道ID格式错误\n\n频道ID应该以 -100 开头，例如：-1003922641317",
                    reply_markup=settings_menu(),
                )
                return

            logger.info(f"Channel {text} bound by admin {user.id}")
            # TODO: Store channel_id in database
            context.user_data["input_mode"] = None
            await update.message.reply_text(
                f"✅ 频道已绑定：{text}\n\n后续备份数据将发送到此频道",
                reply_markup=settings_menu(),
            )

        else:
            # No active input mode, show generic message
            await update.message.reply_text(
                f"📝 收到输入: {text}\n\n请使用按钮操作。",
                reply_markup=main_menu(),
            )

    def run(self) -> None:
        """Run the bot."""
        import asyncio

        async def async_run():
            """Async run method."""
            # Initialize services
            await self.db.init()
            await self.redis.init()
            logger.info("Services initialized")

            # Build application
            self.app = Application.builder().token(self.bot_token).build()

            # Create account service with bot instance
            self.account_service = AccountService(self.db, self.app.bot)
            state_module.account_service = self.account_service

            # Register handlers
            self._register_handlers()

            # Start polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )

            # Keep running
            logger.info("Bot is running...")
            while True:
                await asyncio.sleep(10)

        asyncio.run(async_run())
