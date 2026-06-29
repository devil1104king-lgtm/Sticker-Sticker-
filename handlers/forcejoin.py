from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import register_user, set_user_joined_channel, is_user_banned
import logging

logger = logging.getLogger(__name__)

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if user is allowed to proceed."""
    user = update.effective_user
    if not user:
        logger.warning("No effective user in update.")
        return False

    await register_user(user.id, user.username, user.first_name)

    if await is_user_banned(user.id):
        await update.message.reply_text("🚫 You are banned.")
        return False

    # If no channel is configured, allow immediately.
    if not Config.REQUIRED_CHANNEL:
        logger.info(f"User {user.id} allowed (no channel configured).")
        return True

    try:
        channel = Config.REQUIRED_CHANNEL
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user.id)
        joined = member.status in ["member", "administrator", "creator"]
        await set_user_joined_channel(user.id, joined)
        if joined:
            logger.info(f"User {user.id} is a member of {channel}.")
            return True
        else:
            logger.info(f"User {user.id} not a member of {channel}.")
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel.lstrip('@')}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ You must join our channel to use this bot.\n\n"
                "Please join and then press 'I've Joined ✅'.",
                reply_markup=reply_markup
            )
            return False
    except Exception as e:
        logger.error(f"Force join check failed: {e}")
        # Allow anyway to avoid blocking all users
        await update.message.reply_text("⚠️ Could not verify channel membership. Proceeding anyway.")
        return True
