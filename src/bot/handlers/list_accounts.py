"""List accounts command handler."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.bot.menus.account_menu import account_menu
from src.bot.state import account_service


logger = logging.getLogger(__name__)


async def list_accounts_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /list_accounts command."""
    user = update.effective_user
    logger.info(f"User {user.id} listing accounts")

    # Fetch accounts from database
    if account_service.account_service:
        accounts = await account_service.account_service.list_accounts(
            telegram_id=user.id
        )
    else:
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
        status = "🟢 活跃" if account.get("is_active") else "🔴 停用"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"@{account['username']} ({status})",
                    callback_data=f"account_view_{account['username']}",
                ),
                InlineKeyboardButton(
                    "🗑️", callback_data=f"account_delete_{account['username']}"
                ),
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton("◀️ 返回账号管理", callback_data="main_accounts"),
        ]
    )

    text = f"📋 监控账号列表\n\n共 {len(accounts)} 个账号：\n\n"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
