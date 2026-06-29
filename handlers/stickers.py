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
    user = update.effective_user
    if not user:
        logger.warning("Sticker update without user.")
        return

    logger.info(f"Sticker from {user.id} ({user.username})")

    # Force join check
    if not await check_force_join(update, context):
        logger.info(f"User {user.id} blocked by force join.")
        return

    await register_user(user.id, user.username, user.first_name)

    category = await get_user_category(user.id)
    if not category:
        logger.info(f"User {user.id} has no category. Showing welcome menu.")
        from handlers.start import show_welcome_menu
        await show_welcome_menu(update, context)
        return

    logger.info(f"User {user.id} category: {category}")

    sticker_file_id = await get_random_sticker(category)
    if not sticker_file_id:
        logger.warning(f"No stickers in category '{category}'.")
        await update.message.reply_text(
            f"⚠️ No stickers in '{category}' category yet. Ask admin to add some."
        )
        return

    try:
        await update.message.reply_sticker(sticker_file_id)
        logger.info(f"Replied with sticker to {user.id}")
    except Exception as e:
        logger.error(f"Failed to send sticker: {e}")
        await update.message.reply_text("Sorry, failed to send sticker.")
        return

    await increment_sticker_sent(user.id)
    await log_sticker_activity(update, context, category, sticker_file_id)

async def set_user_category_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str):
    user = update.effective_user
    await set_user_category(user.id, category_name)
    logger.info(f"Set category for {user.id} to {category_name}")

    if update.callback_query:
        query = update.callback_query
        await query.answer(f"Category set to {category_name}")
        await query.edit_message_text(
            f"✅ Category changed to **{category_name}**.\n\n"
            "Now send any sticker to get a random one from this category!",
            reply_markup=None
        )
    else:
        await update.message.reply_text(f"✅ Category set to {category_name}")

async def log_sticker_activity(update, context, category, reply_file_id):
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
        if update.message:
            await context.bot.forward_message(
                chat_id=Config.LOG_GROUP_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        await context.bot.send_sticker(
            chat_id=Config.LOG_GROUP_ID,
            sticker=reply_file_id,
            caption=caption,
            parse_mode="Markdown"
        )
        logger.info(f"Logged sticker activity to group {Config.LOG_GROUP_ID}")
    except Exception as e:
        logger.error(f"Failed to log: {e}")
