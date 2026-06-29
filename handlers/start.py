from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from keyboards.reply import get_main_menu
from utils.decorators import ensure_user, rate_limit

@ensure_user
@rate_limit(seconds=3, command="start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and referral logic."""
    user = update.effective_user
    args = context.args
    
    # Referral Logic
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if referrer_id != user.id:
                success = await db.add_referral(referrer_id, user.id)
                if success:
                    await db.update_coins(referrer_id, Config.REFERRAL_REWARD, "referral_bonus")
                    await db.update_coins(user.id, Config.REFERRAL_REWARD, "referred_bonus")
                    await db.update_user(user.id, ref_by=referrer_id)
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 You referred [{user.first_name}](tg://user?id={user.id}) and earned {Config.REFERRAL_REWARD} coins!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    welcome_text = (
        f"👋 Welcome to the **Sticker Sticker Game Bot**, {user.first_name}!\n\n"
        f"Challenge other players, earn coins, and rank up in the leaderboard.\n\n"
        f"Use the menu below to navigate."
    )
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    
