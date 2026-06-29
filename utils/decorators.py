from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from database import db
from utils.cooldown import cooldown_mgr

def admin_only(func):
    """Decorator to restrict command to admins only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in Config.ADMINS:
            if update.message:
                await update.message.reply_text("⛔ You are not authorized to use this command.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Unauthorized.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def ensure_user(func):
    """Decorator to ensure user exists in the database and is not banned."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
            
        db_user = await db.get_user(user.id)
        if not db_user:
            await db.create_user(user.id, user.username or "", user.first_name or "")
            db_user = await db.get_user(user.id)
            
        if db_user and db_user["is_banned"]:
            if update.message:
                await update.message.reply_text("❌ You are banned from using this bot.")
            elif update.callback_query:
                await update.callback_query.answer("❌ You are banned.", show_alert=True)
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapper

def rate_limit(seconds: int, command: str):
    """Decorator to apply flood protection/cooldowns to handlers."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            is_limited, remaining = cooldown_mgr.check(user_id, command, seconds)
            
            if is_limited:
                msg = f"⏳ Please wait {remaining:.1f} seconds before using this again."
                if update.message:
                    await update.message.reply_text(msg)
                elif update.callback_query:
                    await update.callback_query.answer(msg)
                return
                
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
  
