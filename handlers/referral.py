from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.decorators import ensure_user, rate_limit
from keyboards.inline import close_button_kb

@ensure_user
@rate_limit(seconds=5, command="referral")
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display referral link and information."""
    user = update.effective_user
    db_user = await db.get_user(user.id)
    bot = await context.bot.get_me()
    
    ref_link = f"https://t.me/{bot.username}?start=ref_{user.id}"
    
    text = (
        f"🔗 **Your Referral Link**\n\n"
        f"`{ref_link}`\n\n"
        f"Invite your friends and earn **{Config.REFERRAL_REWARD} 🪙** for each valid signup!\n"
        f"You have invited: **{db_user['ref_count']} friends**."
    )
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=close_button_kb())
  
