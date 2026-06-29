from telegram import Update
from telegram.ext import ContextTypes
from handlers.start import show_welcome_menu
from handlers.stickers import set_user_category_and_notify
from handlers.forcejoin import check_force_join
from handlers.start import help_callback
from database import get_user_category
import logging

logger = logging.getLogger(__name__)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    # Handle force join check
    if data == "check_join":
        # Re-check join status
        # We need to check again - we can just call check_force_join but it expects a message.
        # Since this is a callback, we'll manually check.
        from config import Config
        try:
            channel = Config.REQUIRED_CHANNEL
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

    # Category selection
    if data.startswith("category_"):
        category_name = data.split("_", 1)[1]
        await set_user_category_and_notify(update, context, category_name)
        return

    # Help
    if data == "help":
        await help_callback(update, context)
        return

    # Back to menu
    if data == "back_to_menu":
        await show_welcome_menu(update, context)
        return

    # Default
    await query.edit_message_text("Unknown action.")
