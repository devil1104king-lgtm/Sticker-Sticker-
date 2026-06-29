from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.helpers import format_number, xp_to_level
from utils.decorators import ensure_user, rate_limit
from keyboards.inline import close_button_kb

@ensure_user
@rate_limit(seconds=5, command="profile")
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display user profile and statistics."""
    user = update.effective_user
    db_user = await db.get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("Error fetching profile.")
        return

    level, current_xp, next_level_xp = xp_to_level(db_user["xp"])
    
    # Check if level up occurred
    if level > db_user["level"]:
        await db.update_user(user.id, level=level)
        
    win_rate = db_user["win_rate"]

    profile_text = (
        f"👤 **Profile for {user.first_name}**\n\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🪙 **Coins:** {format_number(db_user['coins'])}\n"
        f"🎖 **Level:** {level}\n"
        f"✨ **XP:** {format_number(db_user['xp'])} (Next: {format_number(current_xp)}/{format_number(next_level_xp)})\n\n"
        f"📊 **Statistics**\n"
        f"🎮 Total Games: {db_user['total_games']}\n"
        f"🏆 Wins: {db_user['wins']}\n"
        f"💀 Losses: {db_user['losses']}\n"
        f"📈 Win Rate: {win_rate:.1f}%\n"
        f"👥 Referrals: {db_user['ref_count']}"
    )

    await update.message.reply_text(
        text=profile_text,
        reply_markup=close_button_kb(),
        parse_mode="Markdown"
    )
  
