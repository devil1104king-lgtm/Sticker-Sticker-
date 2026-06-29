from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import register_user, get_user, set_user_joined_channel, is_user_banned
import logging

logger = logging.getLogger(__name__)

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if the user has joined the required channel.
    Returns True if joined (or not required), False otherwise.
    Also updates the database.
    """
    user = update.effective_user
    if not user:
        return False

    # Register user if new
    await register_user(user.id, user.username, user.first_name)

    # Check if user is banned
    if await is_user_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return False

    # If no channel is configured, allow.
    if not Config.REQUIRED_CHANNEL:
        return True

    try:
        # Get channel info
        channel = Config.REQUIRED_CHANNEL
        # Try to get chat member
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user.id)
        joined = member.status in ["member", "administrator", "creator"]
        await set_user_joined_channel(user.id, joined)
        if joined:
            return True
        else:
            # Show join button
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel.lstrip('@')}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ You must join our channel to use this bot.\n\n"
                "Please join the channel below and then press 'I've Joined ✅'.",
                reply_markup=reply_markup
            )
            return False
    except Exception as e:
        logger.error(f"Force join check failed: {e}")
        # If cannot check (e.g., bot not admin?), allow? But better to let user know.
        await update.message.reply_text(
            "⚠️ Could not verify your channel membership. Please try again later."
        )
        return False
