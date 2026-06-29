import os
import sys
import time
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.decorators import admin_only
from utils.logger import log

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display admin statistics."""
    users = await db.execute_query("SELECT COUNT(*) FROM users")
    total_users = users[0][0]
    
    games = await db.execute_query("SELECT COUNT(*) FROM match_history")
    total_games = games[0][0]

    stats = (
        f"🛠 **Admin Panel**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🎮 Total Matches: {total_games}\n\n"
        f"**Commands:**\n"
        f"`/givecoins <user_id> <amount>`\n"
        f"`/ban <user_id>`\n"
        f"`/unban <user_id>`\n"
        f"`/broadcast <message>`\n"
        f"`/backup`\n"
        f"`/restart`"
    )
    await update.message.reply_text(stats, parse_mode="Markdown")

@admin_only
async def give_coins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to add coins."""
    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
        await db.update_coins(user_id, amount, "admin_give")
        await update.message.reply_text(f"✅ Gave {amount} coins to user {user_id}.")
        log.info(f"Admin {update.effective_user.id} gave {amount} coins to {user_id}")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /givecoins <user_id> <amount>")

@admin_only
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user."""
    try:
        user_id = int(context.args[0])
        await db.update_user(user_id, is_banned=1)
        await update.message.reply_text(f"✅ User {user_id} banned.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /ban <user_id>")

@admin_only
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user."""
    try:
        user_id = int(context.args[0])
        await db.update_user(user_id, is_banned=0)
        await update.message.reply_text(f"✅ User {user_id} unbanned.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /unban <user_id>")

@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast message to all users."""
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message or type `/broadcast <msg>`.")
        return

    users = await db.execute_query("SELECT user_id FROM users")
    msg = update.message.reply_to_message.text if update.message.reply_to_message else " ".join(context.args)
    
    await update.message.reply_text("📢 Broadcast started...")
    
    success, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u["user_id"], text=msg, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05) # Prevent flood wait
        except Exception:
            failed += 1
            
    await db.execute_query("INSERT INTO broadcast_logs (admin_id, total_sent, timestamp) VALUES (?, ?, ?)",
                           (update.effective_user.id, success, time.time()))
    await update.message.reply_text(f"✅ Broadcast complete.\nSent: {success}\nFailed: {failed}")

@admin_only
async def backup_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send database file to Admin."""
    if os.path.exists(Config.DATABASE_NAME):
        await update.message.reply_document(document=open(Config.DATABASE_NAME, "rb"))
    else:
        await update.message.reply_text("⚠️ Database file not found.")

@admin_only
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the bot process."""
    await update.message.reply_text("🔄 Restarting bot...")
    os.execv(sys.executable, ['python'] + sys.argv)
