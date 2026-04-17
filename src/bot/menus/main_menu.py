"""Main menu - Primary navigation menu."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    """Build the main menu keyboard with 4 navigation buttons.

    Returns:
        InlineKeyboardMarkup: Main menu with account, backup, settings, and status buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton("📋 账号管理", callback_data="main_accounts"),
            InlineKeyboardButton("🔄 立即备份", callback_data="main_backup"),
        ],
        [
            InlineKeyboardButton("⚙️ 设置", callback_data="main_settings"),
            InlineKeyboardButton("📊 状态", callback_data="main_status"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
