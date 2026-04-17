"""Start command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.menus.main_menu import main_menu
from src.config import settings


logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    logger.info(f"/start from user {user.id} ({user.username})")

    version = settings.get_version()

    welcome_text = f"""🤖 **Twitter Backup Bot** {version}

━━━━━━━━━━━━━━━━━━━━━━━
欢迎使用 Twitter 备份机器人！
━━━━━━━━━━━━━━━━━━━━━━━

**功能：**
• 📊 监控 Twitter 博主新帖子
• 🔄 自适应检查间隔（高频博主更频繁检查）
• 📥 备份推文、图片、视频、GIF
• 🔒 数据存储在您的私有 Telegram 频道

**使用方式：**
点击下方按钮或发送命令

⚠️ 首次使用需要创建私有频道，机器人会引导您操作"""

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
