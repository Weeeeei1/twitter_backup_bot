"""List accounts command handler."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.account_menu import account_menu


logger = logging.getLogger(__name__)


async def list_accounts_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /list_accounts command."""
    user = update.effective_user
    logger.info(f"User {user.id} listing accounts")

    # TODO: Fetch from database
    accounts = []

    if not accounts:
        await update.message.reply_text(
            "📋 监控账号列表\n\n暂无监控账号。\n\n点击下方按钮添加账号：",
            reply_markup=account_menu(),
        )
        return

    # Build account list with inline buttons
    keyboard = []
    for account in accounts:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"@{account['username']}",
                    callback_data=f"account_view_{account['username']}",
                ),
                InlineKeyboardButton(
                    "🗑️ 删除", callback_data=f"account_delete_{account['username']}"
                ),
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton("◀️ 返回账号管理", callback_data="main_accounts"),
        ]
    )

    text = "📋 监控账号列表\n\n"
    for i, account in enumerate(accounts, 1):
        text += f"{i}. @{account['username']} - {account['status']}\n"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
