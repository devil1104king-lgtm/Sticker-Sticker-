from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from keyboards.inline import game_request_kb
from utils.decorators import ensure_user, rate_limit

@ensure_user
@rate_limit(seconds=10, command="challenge")
async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiate a sticker battle challenge against a replied-to user or mentioned username."""
    challenger = update.effective_user
    message = update.message
    
    challenged_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        challenged_user = message.reply_to_message.from_user
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                challenged_user = entity.user
                
    if not challenged_user:
        await message.reply_text("⚠️ Reply to a user's message to challenge them!")
        return
        
    if challenged_user.id == challenger.id:
        await message.reply_text("⚠️ You cannot challenge yourself.")
        return
        
    if challenged_user.is_bot:
        await message.reply_text("⚠️ You cannot challenge bots.")
        return

    # Check challenger balance
    c_db_user = await db.get_user(challenger.id)
    if c_db_user["coins"] < Config.GAME_LOSER_PENALTY:
        await message.reply_text(f"⚠️ You need at least {Config.GAME_LOSER_PENALTY} coins to challenge someone.")
        return

    text = (
        f"⚔️ **Sticker Battle Challenge!** ⚔️\n\n"
        f"[{challenger.first_name}](tg://user?id={challenger.id}) has challenged "
        f"[{challenged_user.first_name}](tg://user?id={challenged_user.id})!\n\n"
        f"Do you accept the challenge?"
    )
    
    await message.reply_text(
        text,
        reply_markup=game_request_kb(challenger.id, challenged_user.id),
        parse_mode="Markdown"
    )
  
