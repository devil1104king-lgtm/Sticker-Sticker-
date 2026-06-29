from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from utils.helpers import format_number
from utils.decorators import ensure_user, rate_limit

@ensure_user
@rate_limit(seconds=10, command="leaderboard")
async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display global top players."""
    top_users = await db.get_top_users(order_by="coins", limit=10)
    
    if not top_users:
        await update.message.reply_text("Leaderboard is currently empty.")
        return

    text = "🏆 **Top 10 Richest Players** 🏆\n\n"
    for idx, u in enumerate(top_users, start=1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        name = u["first_name"] or u["username"] or "Unknown"
        text += f"{medal} [{name}](tg://user?id={u['user_id']}) - {format_number(u['coins'])} 🪙\n"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Top XP", callback_data="lb_xp"), InlineKeyboardButton("Top Wins", callback_data="lb_wins")],
        [InlineKeyboardButton("✖️ Close", callback_data="close_message")]
    ])

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
      
