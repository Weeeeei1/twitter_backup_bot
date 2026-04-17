"""Add account command handler."""

import logging
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.account_menu import account_menu


logger = logging.getLogger(__name__)


async def add_account_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /add_account command."""
    user = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "📝 **添加监控账号**\n\n"
            "用法：/add_account @用户名\n\n"
            "示例：/add_account elonmusk",
            reply_markup=account_menu(),
            parse_mode="Markdown",
        )
        return

    # Extract username
    username = context.args[0].lstrip("@")

    # Validate username
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await update.message.reply_text(
            "❌ 用户名格式不正确\n\n请提供有效的 Twitter 用户名（不带@）",
            reply_markup=account_menu(),
            parse_mode="Markdown",
        )
        return

    logger.info(f"User {user.id} adding account: {username}")

    # TODO: Add to database and start monitoring
    await update.message.reply_text(
        f"✅ **账号已添加**\n\n"
        f"开始监控：@{username}\n\n"
        f"新帖子会自动备份到您的私有频道。",
        reply_markup=account_menu(),
        parse_mode="Markdown",
    )
