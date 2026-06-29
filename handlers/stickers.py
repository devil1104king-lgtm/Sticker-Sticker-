from telegram import Update
from telegram.ext import ContextTypes
from database import (
    get_user_category, set_user_category, get_random_sticker,
    increment_sticker_sent, increment_sticker_received,
    register_user, get_user, get_all_categories
)
from handlers.forcejoin import check_force_join
from config import Config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming sticker messages."""
    user = update.effective_user
    if not user:
        return

    # Force join check
    if not await check_force_join(update, context):
        return

    # Ensure user is registered
    await register_user(user.id, user.username, user.first_name)

    # Get user's selected category
    category = await get_user_category(user.id)
    if not category:
        # If no category set, ask to select one
        from handlers.start import show_welcome_menu
        await show_welcome_menu(update, context)
        return

    # Get a random sticker from that category
    sticker_file_id = await get_random_sticker(category)
    if not sticker_file_id:
        await update.message.reply_text(
            f"⚠️ No stickers in '{category}' category yet. Please ask admin to add some."
        )
        return

    # Send the sticker reply
    try:
        await update.message.reply_sticker(sticker_file_id)
    except Exception as e:
        logger.error(f"Failed to send sticker: {e}")
        await update.message.reply_text("Sorry, failed to send sticker. Please try again.")
        return

    # Update stats
    await increment_sticker_sent(user.id)
    # The receiver is the bot itself? Not needed.

    # Log to log group
    await log_sticker_activity(update, context, category, sticker_file_id)

async def set_user_category_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str):
    """Set category for user and send confirmation."""
    user = update.effective_user
    await set_user_category(user.id, category_name)
    # Confirm via callback or message
    if update.callback_query:
        query = update.callback_query
        await query.answer(f"Category set to {category_name}")
        await query.edit_message_text(
            f"✅ Category changed to **{category_name}**.\n\n"
            "Now send any sticker to get a random one from this category!",
            reply_markup=None
        )
        # Optionally, show menu again after a while? We'll leave as is.
    else:
        await update.message.reply_text(f"✅ Category set to {category_name}")

async def log_sticker_activity(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, reply_file_id: str):
    """Send logs to LOG_GROUP_ID."""
    if not Config.LOG_GROUP_ID:
        return
    user = update.effective_user
    if not user:
        return

    user_info = f"User: {user.first_name} (@{user.username or 'N/A'}) [ID: {user.id}]"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caption = (
        f"📊 **Sticker Activity**\n"
        f"{user_info}\n"
        f"Category: {category}\n"
        f"Time: {time_str}"
    )

    try:
        # Forward user's sticker and bot's reply sticker to log group
        # We'll forward the user's message (sticker) and then send bot's sticker with caption.
        # But forwarding might fail if user restricts. We'll copy.
        # First, forward user's sticker
        if update.message:
            await context.bot.forward_message(
                chat_id=Config.LOG_GROUP_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        # Then send bot's reply sticker with caption
        await context.bot.send_sticker(
            chat_id=Config.LOG_GROUP_ID,
            sticker=reply_file_id,
            caption=caption,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to log sticker activity: {e}")
