"""Backup command handler."""

import logging
import re

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def backup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /backup command."""
    if not context.args:
        await update.message.reply_text(
            "📥 **立即备份**\n\n"
            "用法：/backup @用户名\n\n"
            "示例：/backup elonmusk\n\n"
            "这将立即抓取并备份该博主的所有推文。",
            parse_mode="Markdown",
        )
        return

    username = context.args[0].lstrip("@")

    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await update.message.reply_text("❌ 用户名格式不正确", parse_mode="Markdown")
        return

    logger.info(f"Backup requested for: {username}")

    # TODO: Trigger backup
    await update.message.reply_text(
        f"🔄 **开始备份**\n\n"
        f"正在抓取 @{username} 的推文...\n\n"
        f"这可能需要几分钟，请稍候。",
        parse_mode="Markdown",
    )
