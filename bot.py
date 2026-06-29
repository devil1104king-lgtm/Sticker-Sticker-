#!/usr/bin/env python3
import asyncio
import os
from threading import Thread
from flask import Flask
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from config import Config
from database import init_db
from handlers.start import start_command
from handlers.stickers import sticker_handler
from handlers.callback import callback_handler
from handlers.admin import (
    stats_command,
    add_sticker_start,
    add_sticker_category,
    add_sticker_receive,
    cancel_add,
    remove_sticker_command,
    handle_sticker_removal,
    list_stickers_command,
    new_category_command,
    delete_category_command,
    broadcast_command,
    ban_command,
    unban_command,
    set_channel_command,
    set_log_group_command,
    export_command,
    backup_command,
    admin_panel,
    admin_callback,
    CATEGORY_SELECT,
    STICKER_RECEIVE
)
from handlers.errors import error_handler
from utils.logger import logger

# ------ Optional web server for Render/Railway ------
app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---------------------------------------------------

async def main():
    """Main async entry point."""
    # Initialize database
    await init_db()

    # Build application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # ----- Handlers -----

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("liststickers", list_stickers_command))
    application.add_handler(CommandHandler("newcategory", new_category_command))
    application.add_handler(CommandHandler("delcategory", delete_category_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("setchannel", set_channel_command))
    application.add_handler(CommandHandler("setlog", set_log_group_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("admin", admin_panel))

    # Sticker handler
    application.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(callback_handler, pattern="^(?!admin_).*"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_.*"))

    # Text handler for removing sticker (admin)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_removal))

    # Conversation for adding sticker
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("addsticker", add_sticker_start),
            CallbackQueryHandler(add_sticker_category, pattern="^(addcat_|cancel_add)")
        ],
        states={
            CATEGORY_SELECT: [CallbackQueryHandler(add_sticker_category, pattern="^(addcat_|cancel_add)")],
            STICKER_RECEIVE: [MessageHandler(filters.Sticker.ALL, add_sticker_receive)]
        },
        fallbacks=[CommandHandler("cancel", cancel_add)]
    )
    application.add_handler(conv_handler)

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot started polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.idle()

if __name__ == "__main__":
    # Start web server if PORT env var is set (for Render/Railway)
    if os.environ.get("PORT"):
        Thread(target=run_web, daemon=True).start()
    # Run the bot's async main
    asyncio.run(main())
