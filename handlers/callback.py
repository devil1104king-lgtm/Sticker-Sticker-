from telegram import Update
from telegram.ext import ContextTypes
from handlers.start import show_welcome_menu
from handlers.stickers import set_user_category_and_notify
from handlers.forcejoin import check_force_join
from handlers.start import help_callback
from database import get_user_category
from config import Config
import logging

logger = logging.getLogger(__name__)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    logger.info(f"Callback from {user.id}: {data}")

    if data == "check_join":
        try:
            channel = Config.REQUIRED_CHANNEL
            if not channel:
                await query.edit_message_text("✅ No channel required.")
                await show_welcome_menu(update, context)
                return
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user.id)
            joined = member.status in ["member", "administrator", "creator"]
            from database import set_user_joined_channel
            await set_user_joined_channel(user.id, joined)
            if joined:
                await query.edit_message_text("✅ You have joined! Welcome.")
                await show_welcome_menu(update, context)
            else:
                await query.answer("You haven't joined yet. Please join first.", show_alert=True)
        except Exception as e:
            logger.error(f"Join check error: {e}")
            await query.answer("Error checking membership. Try again later.", show_alert=True)
        return

    if data.startswith("category_"):
        category_name = data.split("_", 1)[1]
        await set_user_category_and_notify(update, context, category_name)
        return

    if data == "help":
        await help_callback(update, context)
        return

    if data == "back_to_menu":
        await show_welcome_menu(update, context)
        return

    await query.edit_message_text("Unknown action.")
