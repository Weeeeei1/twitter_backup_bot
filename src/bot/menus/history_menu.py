"""History menu - Time range selection for history retrieval."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def history_menu(username: str) -> InlineKeyboardMarkup:
    """Build the history time range selection keyboard.

    Args:
        username: Twitter username to fetch history for.

    Returns:
        InlineKeyboardMarkup: History menu with time range options.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📅 最近一周", callback_data=f"history_{username}_week"
            ),
            InlineKeyboardButton(
                "📆 最近一月", callback_data=f"history_{username}_month"
            ),
        ],
        [
            InlineKeyboardButton(
                "📅 最近一年", callback_data=f"history_{username}_3months"
            ),
            InlineKeyboardButton(
                "📜 全部历史", callback_data=f"history_{username}_year"
            ),
        ],
        [
            InlineKeyboardButton("🗂️ 最近一年", callback_data=f"history_{username}_all"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
