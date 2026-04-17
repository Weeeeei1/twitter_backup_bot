"""Bot menus module - Inline keyboard menus for button-based interactions."""

from src.bot.menus.main_menu import main_menu
from src.bot.menus.account_menu import account_menu
from src.bot.menus.history_menu import history_menu
from src.bot.menus.settings_menu import settings_menu

__all__ = [
    "main_menu",
    "account_menu",
    "history_menu",
    "settings_menu",
]
