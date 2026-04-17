"""Help command handler."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.main_menu import main_menu


logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📖 **帮助信息**

**快速开始：**
1. 点击下方「📋 账号管理」添加要监控的推特账号
2. 机器人会自动监控新帖子
3. 新帖子会发送到您的私有频道

**按钮操作：**
• 📋 账号管理 - 添加/查看/移除监控账号
• 🔄 立即备份 - 手动备份推文
• ⚙️ 设置 - 配置私有频道等
• 📊 状态 - 查看监控统计

**关于监控间隔：**
机器人会自动调整检查间隔：
• 发帖频繁的博主：更频繁检查（最高每分钟）
• 发帖稀少的博主：降低检查频率（最低每小时）

**数据安全：**
• 所有数据存储在您私有的 Telegram 频道
• 只有您和机器人可以访问
"""

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
