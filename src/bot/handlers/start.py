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

    version = settings.get_version()

    welcome_text = f"""
🤖 **Twitter Backup Bot** {version}

━━━━━━━━━━━━━━━━━━━━━━
欢迎使用 Twitter 备份机器人！
━━━━━━━━━━━━━━━━━━━━━━

**功能：**
• 📊 监控 Twitter 博主新帖子
• 🔄 自适应检查间隔（高频博主更频繁检查）
• 📥 备份推文、图片、视频、GIF
• 🔒 数据存储在您的私有 Telegram 频道

**命令：**
• /help - 显示帮助信息
• /add_account @用户名 - 添加监控账号
• /list_accounts - 列出监控账号
• /remove_account @用户名 - 移除监控账号
• /status - 查看状态
• /backup @用户名 - 立即备份博主推文
• /history @用户名 - 获取历史推文

**开始使用：**
1️⃣ 使用 /add_account @用户名 添加要监控的账号
2️⃣ 机器人会自动监控并备份新推文
3️⃣ 使用 /status 查看监控状态

⚠️ 首次使用需要创建私有频道，机器人会引导您操作

**使用前请先阅读 /help**
"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")
