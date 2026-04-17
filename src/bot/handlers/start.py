"""Start command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config import settings


logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    logger.info(f"/start from user {user.id} ({user.username})")

    welcome_text = f"""
🤖 **Twitter Backup Bot** {settings.get_version()}

欢迎使用 Twitter 备份机器人！

**功能：**
• 📊 监控 Twitter 博主新帖子
• 🔄 自适应检查间隔
• 📥 备份推文、图片、视频
• 🔒 数据存储在私有频道

**命令：**
• /help - 显示帮助信息
• /add_account @username - 添加监控账号
• /list_accounts - 列出监控账号
• /remove_account @username - 移除监控账号
• /status - 查看状态
• /backup @username - 备份博主推文
• /history @username - 获取历史推文

**使用前请先阅读 /help**
"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")
