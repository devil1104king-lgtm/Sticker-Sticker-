import os
import io
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import Config
from database import (
    get_all_users, get_total_users, get_total_stickers, get_category_count,
    get_all_categories, get_category_by_name, create_category, delete_category,
    add_sticker, remove_sticker, get_stickers_by_category, get_all_stickers,
    ban_user, unban_user, is_user_banned, export_database,
    get_user, get_user_stats
)
from utils.filters import admin_filter
from utils.helpers import parse_channel_link
import logging

logger = logging.getLogger(__name__)

# Conversation states for adding sticker
CATEGORY_SELECT, STICKER_RECEIVE = range(2)

async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is owner."""
    user = update.effective_user
    if user.id != Config.OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized to use admin commands.")
        return False
    return True

# ----- Stats Command -----

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    total_users = await get_total_users()
    total_stickers = await get_total_stickers()
    total_cats = await get_category_count()
    text = (
        f"📊 **Bot Statistics**\n"
        f"👤 Total Users: {total_users}\n"
        f"🏷️ Total Categories: {total_cats}\n"
        f"🖼️ Total Stickers: {total_stickers}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ----- Add Sticker (Conversation) -----

async def add_sticker_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return ConversationHandler.END
    categories = await get_all_categories()
    if not categories:
        await update.message.reply_text("No categories available. Create one first with /newcategory.")
        return ConversationHandler.END

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"addcat_{cat['name']}")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_add")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a category to add sticker to.\n\n"
        "Or send /cancel to cancel.",
        reply_markup=reply_markup
    )
    return CATEGORY_SELECT

async def add_sticker_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel_add":
        await query.edit_message_text("Operation cancelled.")
        return ConversationHandler.END
    if data.startswith("addcat_"):
        cat_name = data.split("_", 1)[1]
        context.user_data["add_category"] = cat_name
        await query.edit_message_text(
            f"Category: {cat_name}\n\n"
            "Now send me the **sticker** you want to add.\n"
            "Reply to this message with a sticker.\n"
            "Or send /cancel to cancel."
        )
        return STICKER_RECEIVE
    return CATEGORY_SELECT

async def add_sticker_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.sticker:
        await update.message.reply_text("Please send a sticker.")
        return STICKER_RECEIVE
    category = context.user_data.get("add_category")
    if not category:
        await update.message.reply_text("Session expired. Start again with /addsticker.")
        return ConversationHandler.END

    file_id = update.message.sticker.file_id
    file_unique_id = update.message.sticker.file_unique_id
    added_by = update.effective_user.id

    success = await add_sticker(category, file_id, file_unique_id, added_by)
    if success:
        await update.message.reply_text(f"✅ Sticker added to category '{category}' successfully!")
    else:
        await update.message.reply_text("❌ Failed to add sticker. It might already exist or category invalid.")
    # Clear data
    context.user_data.pop("add_category", None)
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    context.user_data.pop("add_category", None)
    return ConversationHandler.END

# ----- Remove Sticker -----

async def remove_sticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    # List all stickers with IDs
    stickers = await get_all_stickers()
    if not stickers:
        await update.message.reply_text("No stickers in database.")
        return
    text = "🗑️ **Remove Sticker**\n\nSend the sticker ID to remove.\n\n"
    for s in stickers[:20]:  # limit display
        text += f"ID: `{s['id']}` - Category: {s['category_name']} - File: {s['file_id'][:10]}...\n"
    if len(stickers) > 20:
        text += f"\n... and {len(stickers)-20} more. Use /liststickers to see all."
    text += "\n\nSend the ID number to delete."
    context.user_data["removing_sticker"] = True
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_sticker_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("removing_sticker"):
        return
    try:
        sticker_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Please send a valid numeric ID.")
        return
    success = await remove_sticker(sticker_id)
    if success:
        await update.message.reply_text(f"✅ Sticker ID {sticker_id} removed.")
    else:
        await update.message.reply_text(f"❌ Sticker ID {sticker_id} not found.")
    context.user_data.pop("removing_sticker", None)

# ----- List Stickers -----

async def list_stickers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    stickers = await get_all_stickers()
    if not stickers:
        await update.message.reply_text("No stickers.")
        return
    text = "📋 **All Stickers**\n\n"
    for s in stickers:
        text += f"ID: `{s['id']}` - Cat: {s['category_name']} - File: {s['file_id'][:15]}...\n"
    # Split if too long
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

# ----- New Category -----

async def new_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /newcategory <name> [emoji]")
        return
    name = args[0]
    emoji = args[1] if len(args) > 1 else ""
    success = await create_category(name, emoji, update.effective_user.id)
    if success:
        await update.message.reply_text(f"✅ Category '{name}' created.")
    else:
        await update.message.reply_text(f"❌ Category '{name}' already exists.")

# ----- Delete Category -----

async def delete_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /delcategory <name>")
        return
    name = args[0]
    success = await delete_category(name)
    if success:
        await update.message.reply_text(f"✅ Category '{name}' deleted.")
    else:
        await update.message.reply_text(f"❌ Category '{name}' not found.")

# ----- Broadcast -----

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message_text = " ".join(context.args)
    users = await get_all_users()
    sent = 0
    failed = 0
    await update.message.reply_text(f"Broadcasting to {len(users)} users...")
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=message_text)
            sent += 1
        except Exception:
            failed += 1
        # Avoid flooding
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Broadcast complete: {sent} sent, {failed} failed.")

# Need import asyncio for sleep
import asyncio

# ----- Ban/Unban -----

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("User not found in database.")
        return
    await ban_user(user_id)
    await update.message.reply_text(f"✅ User {user_id} banned.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("User not found.")
        return
    await unban_user(user_id)
    await update.message.reply_text(f"✅ User {user_id} unbanned.")

# ----- Set Channel -----

async def set_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /setchannel <channel_username_or_id>")
        return
    channel = args[0]
    # Update config? We can store in environment but better store in DB or just update config variable?
    # Since config is read from env, we could persist in a file, but for simplicity, we'll just update the global variable.
    # However, restart will reset. Better store in a separate config table. For this example, we'll just change the variable in memory.
    # But we need to persist? We'll store in DB in a settings table.
    # Let's add a settings table.
    # We'll implement later. For now, just update Config.REQUIRED_CHANNEL and notify.
    Config.REQUIRED_CHANNEL = channel
    await update.message.reply_text(f"✅ Required channel updated to {channel}. (Note: this change is temporary until restart)")

# We'll skip persistent settings for simplicity.

# ----- Set Log Group -----

async def set_log_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /setlog <group_id>")
        return
    try:
        group_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid group ID.")
        return
    Config.LOG_GROUP_ID = group_id
    await update.message.reply_text(f"✅ Log group updated to {group_id}. (temporary until restart)")

# ----- Export Database -----

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    try:
        data = await export_database()
        # Send as file
        await update.message.reply_document(
            document=io.BytesIO(data),
            filename=f"stickers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            caption="📦 Database backup"
        )
    except Exception as e:
        await update.message.reply_text(f"Export failed: {e}")

# ----- Backup (same as export) -----

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await export_command(update, context)

# ----- Admin Panel (callback-based) -----

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("➕ Add Sticker", callback_data="admin_addsticker")],
        [InlineKeyboardButton("➖ Remove Sticker", callback_data="admin_removesticker")],
        [InlineKeyboardButton("📋 List Stickers", callback_data="admin_liststickers")],
        [InlineKeyboardButton("🏷️ New Category", callback_data="admin_newcategory")],
        [InlineKeyboardButton("❌ Delete Category", callback_data="admin_delcategory")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton("🔧 Set Channel", callback_data="admin_setchannel")],
        [InlineKeyboardButton("📝 Set Log Group", callback_data="admin_setlog")],
        [InlineKeyboardButton("💾 Export DB", callback_data="admin_export")],
        [InlineKeyboardButton("💾 Backup DB", callback_data="admin_backup")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠️ **Admin Panel**", reply_markup=reply_markup, parse_mode="Markdown")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not await admin_only(update, context):
        await query.edit_message_text("Unauthorized.")
        return

    # We'll map to existing commands or handle inline
    if data == "admin_stats":
        await stats_command(update, context)
    elif data == "admin_addsticker":
        # Start conversation
        await add_sticker_start(update, context)
    elif data == "admin_removesticker":
        await remove_sticker_command(update, context)
    elif data == "admin_liststickers":
        await list_stickers_command(update, context)
    elif data == "admin_newcategory":
        # Ask for name via callback? We'll just prompt to use /newcategory
        await query.edit_message_text("Use /newcategory <name> [emoji]")
    elif data == "admin_delcategory":
        await query.edit_message_text("Use /delcategory <name>")
    elif data == "admin_broadcast":
        await query.edit_message_text("Use /broadcast <message>")
    elif data == "admin_ban":
        await query.edit_message_text("Use /ban <user_id>")
    elif data == "admin_unban":
        await query.edit_message_text("Use /unban <user_id>")
    elif data == "admin_setchannel":
        await query.edit_message_text("Use /setchannel <channel>")
    elif data == "admin_setlog":
        await query.edit_message_text("Use /setlog <group_id>")
    elif data == "admin_export":
        await export_command(update, context)
    elif data == "admin_backup":
        await backup_command(update, context)
    else:
        await query.edit_message_text("Unknown action.")
