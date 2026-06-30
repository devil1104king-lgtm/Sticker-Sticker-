import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from database import db
from utils.logger import log
from utils.backup import backup_database_job

from handlers.start import start_command
from handlers.profile import profile_command
from handlers.leaderboard import leaderboard_command
from handlers.referral import referral_command
from handlers.game import challenge_command
from handlers.callbacks import callback_router
from handlers.admin import admin_panel, give_coins, ban_user, unban_user, broadcast, backup_db, restart_bot

async def main() -> None:
    await db.init_db()
    app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("challenge", challenge_command))
    
    # Admin
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("givecoins", give_coins))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("backup", backup_db))
    app.add_handler(CommandHandler("restart", restart_bot))

    app.add_handler(CallbackQueryHandler(callback_router))
    
    # Job Queue
    job_queue = app.job_queue
    job_queue.run_repeating(backup_database_job, interval=43200, first=10)

    log.info("Bot is polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
