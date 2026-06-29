import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import Config
from database import db
from utils.logger import log
from utils.backup import backup_database_job

# Handlers
from handlers.start import start_command
from handlers.profile import profile_command
from handlers.leaderboard import leaderboard_command
from handlers.referral import referral_command
from handlers.game import challenge_command
from handlers.callbacks import callback_router
from handlers.admin import (
    admin_panel, give_coins, ban_user, unban_user, broadcast, backup_db, restart_bot
)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and ensure the bot never crashes."""
    log.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An internal error occurred. Administrators have been notified.")
        except Exception:
            pass

async def daily_reward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle daily reward claim."""
    import time
    user_id = update.effective_user.id
    
    # Using execute_query from db directly for custom logic
    res = await db.execute_query("SELECT last_claim_time FROM daily_rewards WHERE user_id = ?", (user_id,))
    current_time = time.time()
    
    if res:
        last_claim = res[0]["last_claim_time"]
        if current_time - last_claim < Config.DAILY_COOLDOWN:
            rem = Config.DAILY_COOLDOWN - (current_time - last_claim)
            hours, remainder = divmod(rem, 3600)
            minutes, _ = divmod(remainder, 60)
            await update.message.reply_text(f"⏳ Come back in {int(hours)}h {int(minutes)}m to claim your next reward!")
            return
            
        await db.execute_query("UPDATE daily_rewards SET last_claim_time = ? WHERE user_id = ?", (current_time, user_id))
    else:
        await db.execute_query("INSERT INTO daily_rewards (user_id, last_claim_time) VALUES (?, ?)", (user_id, current_time))
        
    await db.update_coins(user_id, Config.DAILY_REWARD, "daily_reward")
    await update.message.reply_text(f"🎁 You successfully claimed your daily reward of **{Config.DAILY_REWARD} 🪙**!", parse_mode="Markdown")

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route text button presses from the Reply Keyboard."""
    text = update.message.text
    if text == "🎮 Challenge":
        await update.message.reply_text("To challenge, reply to a user's message with `/challenge` or mention them!")
    elif text == "👤 Profile":
        await profile_command(update, context)
    elif text == "🏆 Leaderboard":
        await leaderboard_command(update, context)
    elif text == "🎁 Daily Reward":
        await daily_reward_handler(update, context)
    elif text == "🔗 Referral":
        await referral_command(update, context)

def main() -> None:
    """Main application initialization and polling."""
    if not Config.BOT_TOKEN:
        log.error("BOT_TOKEN is missing in environment variables.")
        return

    # Create event loop and initialize DB
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(db.init_db())
    log.info("Database initialized successfully.")

    app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("challenge", challenge_command))
    
    # Admin Handlers
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("givecoins", give_coins))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("backup", backup_db))
    app.add_handler(CommandHandler("restart", restart_bot))

    # General Text / Reply Keyboard Router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_router))

    # Callback Query Router for Inline Buttons
    app.add_handler(CallbackQueryHandler(callback_router))

    # Error Handler
    app.add_error_handler(error_handler)

    # Job Queue for Backups (Run every 12 hours)
    job_queue = app.job_queue
    job_queue.run_repeating(backup_database_job, interval=43200, first=10)

    log.info("Bot is polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
  
