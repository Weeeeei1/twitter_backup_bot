"""List accounts command handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes


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
            "📋 监控账号列表\n\n暂无监控账号。\n\n使用 /add_account @用户名 添加账号",
        )
        return

    text = "📋 监控账号列表\n\n"
    for i, account in enumerate(accounts, 1):
        text += f"{i}. @{account['username']} - {account['status']}\n"

    await update.message.reply_text(text)
