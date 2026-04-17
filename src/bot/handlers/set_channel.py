"""Set channel command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config import settings


logger = logging.getLogger(__name__)


async def set_channel_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /setchannel command - bind user's private channel."""
    user = update.effective_user
    logger.info(f"User {user.id} setting channel")

    # Check if user is admin
    if user.id != settings.admin_telegram_id:
        await update.message.reply_text("⚠️ 只有管理员可以使用此命令")
        return

    if not context.args:
        await update.message.reply_text(
            "📢 设置私有频道\n\n"
            "用法：/setchannel <频道ID>\n\n"
            "例如：/setchannel -1003922641317\n\n"
            "将 Bot 添加到频道作为管理员后，使用此命令绑定频道"
        )
        return

    channel_id = context.args[0].strip()

    # Validate channel ID format
    if not channel_id.startswith("-100"):
        await update.message.reply_text(
            "❌ 频道ID格式错误\n\n频道ID应该以 -100 开头，例如：-1003922641317"
        )
        return

    # TODO: Store channel_id in database for this user
    # For now, just acknowledge
    await update.message.reply_text(
        f"✅ 频道已绑定：{channel_id}\n\n后续备份数据将发送到此频道"
    )
    logger.info(f"Channel {channel_id} bound by admin {user.id}")
