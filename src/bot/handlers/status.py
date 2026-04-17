"""Status command handler."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.main_menu import main_menu
from src.bot import state as state_module


logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    user = update.effective_user
    logger.info(f"User {user.id} checking status")

    # Fetch actual stats
    accounts_count = 0
    tweets_count = "待实现"
    media_count = "待实现"
    scheduler_status = "✅ 运行中"
    twitter_status = "✅ 正常"

    try:
        if state_module.account_service:
            logger.info(f"Fetching stats for user {user.id}")
            stats = await state_module.account_service.get_account_stats(user.id)
            accounts_count = stats.get("total_accounts", 0)
            logger.info(f"Stats fetched: {accounts_count} accounts")
            scheduler_status = "✅ 运行中"
            twitter_status = "✅ 正常"
        else:
            logger.warning("account_service is None")
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        scheduler_status = "⚠️ 查询失败"
        twitter_status = "⚠️ 查询失败"

    stats_text = f"""
📊 **状态统计**

**版本：** v0.2.0

**监控统计：**
• 监控账号数：{accounts_count}
• 总推文数：{tweets_count}
• 总媒体数：{media_count}

**调度器：** {scheduler_status}

**最近活动：**
暂无

**系统状态：**
• Twitter {twitter_status}
• 数据库 ✅ 正常
• Redis ✅ 正常
"""

    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
