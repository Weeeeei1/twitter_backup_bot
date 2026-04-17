"""Help command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📖 **帮助信息**

**快速开始：**
1. 使用 /add_account @用户名 添加要监控的推特账号
2. 机器人会自动监控新帖子
3. 新帖子会发送到您的私有频道

**命令说明：**

👤 **账号管理**
• /add_account @username - 添加监控账号
• /list_accounts - 列出已监控账号
• /remove_account @username - 移除监控账号

📥 **备份操作**
• /backup @username - 立即备份博主推文
• /history @username - 获取历史推文
  - 支持时间范围：最近一周、最近一个月、自定义

⚙️ **设置**
• /status - 查看监控状态和统计

**关于监控间隔：**
机器人会自动调整检查间隔：
• 发帖频繁的博主：更频繁检查（最高每分钟）
• 发帖稀少的博主：降低检查频率（最低每小时）

**数据安全：**
• 所有数据存储在您私有的 Telegram 频道
• 只有您和机器人可以访问
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")
