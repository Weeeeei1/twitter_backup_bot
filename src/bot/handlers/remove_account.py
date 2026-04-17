"""Remove account command handler."""

import logging
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.account_menu import account_menu


logger = logging.getLogger(__name__)


async def remove_account_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /remove_account command."""
    if not context.args:
        await update.message.reply_text(
            "📝 **移除监控账号**\n\n"
            "用法：/remove_account @用户名\n\n"
            "示例：/remove_account elonmusk",
            reply_markup=account_menu(),
            parse_mode="Markdown",
        )
        return

    username = context.args[0].lstrip("@")

    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await update.message.reply_text(
            "❌ 用户名格式不正确",
            reply_markup=account_menu(),
            parse_mode="Markdown",
        )
        return

    logger.info(f"Removing account: {username}")

    # TODO: Remove from database
    await update.message.reply_text(
        f"✅ **已移除**\n\n停止监控：@{username}",
        reply_markup=account_menu(),
        parse_mode="Markdown",
    )
