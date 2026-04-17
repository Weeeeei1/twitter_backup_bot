"""Status command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    user = update.effective_user
    logger.info(f"User {user.id} checking status")

    # TODO: Fetch actual stats from database
    stats_text = f"""
📊 **状态统计**

**版本：** v0.1.0

**监控统计：**
• 监控账号数：0
• 总推文数：0
• 总媒体数：0

**最近活动：**
暂无

**系统状态：**
• Twitter 连接：✅ 正常
• 数据库：✅ 正常
• Redis：✅ 正常
"""

    await update.message.reply_text(stats_text, parse_mode="Markdown")
