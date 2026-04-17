"""Settings menu - Bot settings submenu."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def settings_menu() -> InlineKeyboardMarkup:
    """Build the settings submenu keyboard.

    Returns:
        InlineKeyboardMarkup: Settings menu with base, interval, notification, and back buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton("🔧 基础设置", callback_data="settings_base"),
            InlineKeyboardButton("⏱️ 检查间隔", callback_data="settings_interval"),
        ],
        [
            InlineKeyboardButton("📢 通知设置", callback_data="settings_notification"),
        ],
        [
            InlineKeyboardButton("◀️ 返回主菜单", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
