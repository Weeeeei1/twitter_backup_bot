"""History command handler - 获取历史推文."""

import logging
import re
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


# Time range options
TIME_RANGES = {
    "week": ("最近一周", 7),
    "month": ("最近一个月", 30),
    "3months": ("最近三个月", 90),
    "year": ("最近一年", 365),
    "all": ("全部", None),
}


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command with time range selection."""
    if not context.args:
        # Show help with time range options
        await update.message.reply_text(
            "📜 **获取历史推文**\n\n"
            "用法：/history @用户名 [时间范围]\n\n"
            "时间范围选项：\n"
            "• week - 最近一周\n"
            "• month - 最近一个月\n"
            "• 3months - 最近三个月\n"
            "• year - 最近一年\n"
            "• all - 全部\n\n"
            "示例：\n"
            "• /history elonmusk week\n"
            "• /history elonmusk month",
            parse_mode="Markdown",
        )
        return

    username = context.args[0].lstrip("@")

    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await update.message.reply_text("❌ 用户名格式不正确", parse_mode="Markdown")
        return

    # Parse time range
    time_range = "month"  # default
    if len(context.args) > 1:
        time_range = context.args[1].lower()
        if time_range not in TIME_RANGES:
            time_range = "month"

    range_name, days = TIME_RANGES[time_range]

    logger.info(f"History requested for {username}, range: {range_name}")

    # Show confirmation with time range
    keyboard = [
        [
            InlineKeyboardButton("最近一周", callback_data=f"history_{username}_week"),
            InlineKeyboardButton(
                "最近一个月", callback_data=f"history_{username}_month"
            ),
        ],
        [
            InlineKeyboardButton(
                "最近三个月", callback_data=f"history_{username}_3months"
            ),
            InlineKeyboardButton("最近一年", callback_data=f"history_{username}_year"),
        ],
        [
            InlineKeyboardButton("全部历史", callback_data=f"history_{username}_all"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📜 **获取历史推文**\n\n"
        f"账号：@{username}\n"
        f"时间范围：{range_name}\n\n"
        f"请选择时间范围或使用按钮确认：",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
