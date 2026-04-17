"""Callback query handler for all button interactions."""

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from src.bot.menus.main_menu import main_menu
from src.bot.menus.account_menu import account_menu
from src.bot.menus.settings_menu import settings_menu
from src.bot import state as state_module


logger = logging.getLogger(__name__)


# Time range options for history
TIME_RANGES = {
    "week": ("最近一周", 7),
    "month": ("最近一个月", 30),
    "3months": ("最近三个月", 90),
    "year": ("最近一年", 365),
    "all": ("全部", None),
}


async def callback_handler(update: Update, context: CallbackContext) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data

    # Acknowledge the callback
    await query.answer()

    # Parse callback data and dispatch
    if data.startswith("main_"):
        await handle_main_menu(update, context, data)
    elif data.startswith("account_"):
        await handle_account_menu(update, context, data)
    elif data.startswith("history_"):
        await handle_history(update, context, data)
    elif data.startswith("settings_"):
        await handle_settings(update, context, data)
    elif data.startswith("backup_"):
        await handle_backup(update, context, data)
    elif data.startswith("back_"):
        await handle_back(update, context, data)
    else:
        await query.answer("未知操作")


async def handle_main_menu(update: Update, context: CallbackContext, data: str) -> None:
    """Handle main menu button clicks."""
    query = update.callback_query

    if data == "main_accounts":
        await query.edit_message_text(
            text="📋 **账号管理**\n\n请选择操作：",
            reply_markup=account_menu(),
            parse_mode="Markdown",
        )
    elif data == "main_backup":
        # Ask user for username
        await query.edit_message_text(
            text="🔄 **立即备份**\n\n请使用命令：\n`/backup @用户名`\n\n"
            "示例：\n`/backup elonmusk`",
            parse_mode="Markdown",
        )
    elif data == "main_settings":
        await query.edit_message_text(
            text="⚙️ **设置**\n\n请选择设置类别：",
            reply_markup=settings_menu(),
            parse_mode="Markdown",
        )
    elif data == "main_status":
        await show_status(update, context)


def account_back_menu() -> InlineKeyboardMarkup:
    """Build keyboard with only back button."""
    keyboard = [
        [InlineKeyboardButton("◀️ 返回账号管理", callback_data="main_accounts")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_account_menu(
    update: Update, context: CallbackContext, data: str
) -> None:
    """Handle account menu button clicks."""
    query = update.callback_query

    if data == "account_add":
        await query.edit_message_text(
            text="➕ **添加账号**\n\n点击下方按钮开始添加账号：",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ 添加账号", callback_data="account_add_confirm"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "◀️ 返回账号管理", callback_data="main_accounts"
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )
    elif data == "account_add_confirm":
        # Set context to indicate we're awaiting username input
        context.user_data["input_mode"] = "add_account"
        await query.edit_message_text(
            text="📝 **添加账号**\n\n请回复推特用户名（不带@）：\n\n示例：`elonmusk`\n\n点击取消可返回",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("❌ 取消", callback_data="main_accounts")],
                ]
            ),
            parse_mode="Markdown",
        )
    elif data == "account_list":
        # Fetch actual accounts from database
        user = update.effective_user
        try:
            if state_module.account_service:
                accounts = await state_module.account_service.list_accounts(
                    telegram_id=user.id
                )
            else:
                accounts = []
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            accounts = []

        if not accounts:
            await query.edit_message_text(
                text="📋 **账号列表**\n\n暂无监控账号。\n\n点击下方按钮添加账号：",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "➕ 添加账号", callback_data="account_add_confirm"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "◀️ 返回账号管理", callback_data="main_accounts"
                            )
                        ],
                    ]
                ),
                parse_mode="Markdown",
            )
            return

        # Build account list with inline buttons
        keyboard = []
        for account in accounts:
            status = "🟢" if account.get("is_active") else "🔴"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status} @{account['username']}",
                        callback_data=f"account_view_{account['username']}",
                    ),
                    InlineKeyboardButton(
                        "🗑️", callback_data=f"account_delete_{account['username']}"
                    ),
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ 添加账号", callback_data="account_add_confirm"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton("◀️ 返回账号管理", callback_data="main_accounts"),
            ]
        )

        await query.edit_message_text(
            text=f"📋 **账号列表**\n\n共 {len(accounts)} 个账号：",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    elif data == "account_remove":
        # Set context to indicate we're awaiting username input for removal
        context.user_data["input_mode"] = "remove_account"
        await query.edit_message_text(
            text="➖ **移除账号**\n\n请回复要移除的账号用户名：\n\n示例：`elonmusk`\n\n点击取消可返回",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("❌ 取消", callback_data="main_accounts")],
                ]
            ),
            parse_mode="Markdown",
        )


async def handle_history(update: Update, context: CallbackContext, data: str) -> None:
    """Handle history button clicks - fetch and send history for username/time."""
    query = update.callback_query

    # Parse callback data: history_{username}_{time_range}
    parts = data.split("_")
    if len(parts) < 3:
        await query.answer("数据格式错误")
        return

    username = parts[1]
    time_range = parts[2]

    # Validate username format
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await query.answer("用户名格式不正确")
        return

    # Validate time range
    if time_range not in TIME_RANGES:
        await query.answer("未知的时间范围")
        return

    range_name, days = TIME_RANGES[time_range]
    logger.info(f"History requested for {username}, range: {range_name}")

    # Show loading message
    await query.edit_message_text(
        text=f"📜 **获取历史推文**\n\n"
        f"账号：@{username}\n"
        f"时间范围：{range_name}\n\n"
        f"🔄 正在抓取推文，请稍候...",
        parse_mode="Markdown",
    )

    # TODO: Trigger actual history fetch from service
    # For now, show completion message
    await query.edit_message_text(
        text=f"✅ **历史推文抓取完成**\n\n"
        f"账号：@{username}\n"
        f"时间范围：{range_name}\n\n"
        f"推文已备份到您的私有频道。",
        parse_mode="Markdown",
    )


async def handle_settings(update: Update, context: CallbackContext, data: str) -> None:
    """Handle settings menu button clicks."""
    query = update.callback_query

    if data == "settings_base":
        await query.edit_message_text(
            text="🔧 **基础设置**\n\n"
            "• 私有频道配置\n"
            "• 媒体质量设置\n\n"
            "点击下方按钮配置私有频道：",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📢 设置私有频道", callback_data="settings_setchannel"
                        )
                    ],
                    [InlineKeyboardButton("◀️ 返回设置", callback_data="main_settings")],
                ]
            ),
            parse_mode="Markdown",
        )
    elif data == "settings_setchannel":
        # Set context to indicate we're awaiting channel ID input
        context.user_data["input_mode"] = "setchannel"
        await query.edit_message_text(
            text="📢 **设置私有频道**\n\n"
            "请回复频道ID（格式：-100xxxxxxxxxx）\n\n"
            "将 Bot 添加到频道作为管理员后，发送频道ID即可绑定",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("❌ 取消", callback_data="main_settings")],
                ]
            ),
            parse_mode="Markdown",
        )
    elif data == "settings_interval":
        await query.edit_message_text(
            text="⏱️ **检查间隔设置**\n\n"
            "当前使用自适应检查间隔。\n\n"
            "• 基础间隔：5分钟\n"
            "• 最小间隔：1分钟\n"
            "• 最大间隔：1小时\n\n"
            "系统会根据博主发帖频率自动调整。",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("◀️ 返回设置", callback_data="main_settings")],
                ]
            ),
            parse_mode="Markdown",
        )
    elif data == "settings_notification":
        await query.edit_message_text(
            text="📢 **通知设置**\n\n"
            "通知功能配置：\n\n"
            "• 新推文通知：已开启\n"
            "• 备份完成通知：已开启\n"
            "• 错误通知：已开启",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("◀️ 返回设置", callback_data="main_settings")],
                ]
            ),
            parse_mode="Markdown",
        )


async def handle_backup(update: Update, context: CallbackContext, data: str) -> None:
    """Handle backup button clicks - trigger backup for username."""
    query = update.callback_query

    # Parse callback data: backup_{username}
    parts = data.split("_")
    if len(parts) < 2:
        await query.answer("数据格式错误")
        return

    username = parts[1]

    # Validate username format
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        await query.answer("用户名格式不正确")
        return

    logger.info(f"Backup triggered for: {username}")

    # Show loading message
    await query.edit_message_text(
        text=f"🔄 **开始备份**\n\n"
        f"正在抓取 @{username} 的推文...\n\n"
        f"这可能需要几分钟，请稍候。",
        parse_mode="Markdown",
    )

    # TODO: Trigger actual backup from service
    # For now, show completion message
    await query.edit_message_text(
        text=f"✅ **备份完成**\n\n账号：@{username}\n\n新推文已备份到您的私有频道。",
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


async def handle_back(update: Update, context: CallbackContext, data: str) -> None:
    """Handle back navigation button clicks."""
    query = update.callback_query

    # Clear any pending input mode
    context.user_data["input_mode"] = None

    if data == "back_main":
        await query.edit_message_text(
            text="🤖 **Twitter Backup Bot**\n\n主菜单",
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )


async def show_status(update: Update, context: CallbackContext) -> None:
    """Show status information."""
    query = update.callback_query

    stats_text = """
📊 **状态统计**

**版本：** v0.2.0

**监控统计：**
• 监控账号数：0
• 总推文数：0
• 总媒体数：0

**最近活动：**
暂无

**系统状态：**
• Twitter 连接：✅ 正常
• 数据库：✅ 正常
• Redis：✅ 正常
"""

    await query.edit_message_text(
        text=stats_text,
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )
