"""Account menu - Account management submenu."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def account_menu() -> InlineKeyboardMarkup:
    """Build the account management submenu keyboard.

    Returns:
        InlineKeyboardMarkup: Account menu with add, list, remove, and back buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ 添加账号", callback_data="account_add"),
        ],
        [
            InlineKeyboardButton("📋 账号列表", callback_data="account_list"),
        ],
        [
            InlineKeyboardButton("➖ 移除账号", callback_data="account_remove"),
        ],
        [
            InlineKeyboardButton("◀️ 返回主菜单", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
