import random
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.helpers import format_number

async def handle_game_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Accept/Decline callbacks for games."""
    query = update.callback_query
    data = query.data.split("_")
    action, challenger_id, challenged_id = data[1], int(data[2]), int(data[3])
    
    if query.from_user.id != challenged_id:
        await query.answer("⚠️ This challenge is not for you!", show_alert=True)
        return
        
    if action == "decline":
        await query.message.edit_text("❌ The challenge was declined.")
        await query.answer("You declined the challenge.")
        return
        
    if action == "accept":
        await query.answer("Challenge accepted! Processing battle...")
        
        c_db = await db.get_user(challenger_id)
        o_db = await db.get_user(challenged_id)
        
        # Ensure opponent is registered
        if not o_db:
            await db.create_user(challenged_id, query.from_user.username or "", query.from_user.first_name)
            o_db = await db.get_user(challenged_id)
            
        if c_db["coins"] < Config.GAME_LOSER_PENALTY:
            await query.message.edit_text("⚠️ Challenger doesn't have enough coins anymore.")
            return
        if o_db["coins"] < Config.GAME_LOSER_PENALTY:
            await query.message.edit_text("⚠️ You don't have enough coins to accept.")
            return

        # Battle Animation Steps
        animation = ["🎲 Rolling dice...", "⚔️ Clashing stickers...", "🔥 Calculating winner..."]
        for frame in animation:
            await query.message.edit_text(frame)
            await asyncio.sleep(1)

        # Logic: Random Winner
        winner_id = random.choice([challenger_id, challenged_id])
        loser_id = challenged_id if winner_id == challenger_id else challenger_id
        
        # Update DB Stats
        w_db = await db.get_user(winner_id)
        l_db = await db.get_user(loser_id)
        
        # Winner Updates
        new_w_wins = w_db["wins"] + 1
        new_w_total = w_db["total_games"] + 1
        w_win_rate = (new_w_wins / new_w_total) * 100
        await db.update_coins(winner_id, Config.GAME_REWARD_COINS, "won_game")
        await db.update_user(winner_id, xp=w_db["xp"] + Config.GAME_REWARD_XP, wins=new_w_wins, total_games=new_w_total, win_rate=w_win_rate)
        
        # Loser Updates
        new_l_losses = l_db["losses"] + 1
        new_l_total = l_db["total_games"] + 1
        l_win_rate = (l_db["wins"] / new_l_total) * 100
        await db.update_coins(loser_id, -Config.GAME_LOSER_PENALTY, "lost_game")
        await db.update_user(loser_id, losses=new_l_losses, total_games=new_l_total, win_rate=l_win_rate)

        await db.record_match(challenger_id, challenged_id, winner_id)

        result_text = (
            f"🏆 **Battle Finished!** 🏆\n\n"
            f"👑 **Winner:** [{w_db['first_name']}](tg://user?id={winner_id})\n"
            f"Earned: {Config.GAME_REWARD_COINS} 🪙 | {Config.GAME_REWARD_XP} XP\n\n"
            f"💀 **Loser:** [{l_db['first_name']}](tg://user?id={loser_id})\n"
            f"Lost: {Config.GAME_LOSER_PENALTY} 🪙"
        )
        await query.message.edit_text(result_text, parse_mode="Markdown")

async def handle_general_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle global buttons like close or pagination."""
    query = update.callback_query
    data = query.data
    
    if data == "close_message":
        try:
            await query.message.delete()
        except Exception:
            await query.answer("Could not delete message.")
        return
        
    if data.startswith("lb_"):
        mode = data.split("_")[1]
        order_col = "xp" if mode == "xp" else "wins"
        top_users = await db.get_top_users(order_by=order_col, limit=10)
        
        title = "Top XP" if mode == "xp" else "Top Wins"
        text = f"🏆 **{title} Players** 🏆\n\n"
        for idx, u in enumerate(top_users, start=1):
            name = u["first_name"] or u["username"] or "Unknown"
            val = format_number(u[order_col])
            text += f"{idx}. [{name}](tg://user?id={u['user_id']}) - {val}\n"
            
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Top Coins", callback_data="lb_coins"), 
             InlineKeyboardButton("Top XP" if mode == "wins" else "Top Wins", callback_data=f"lb_{'xp' if mode == 'wins' else 'wins'}")],
            [InlineKeyboardButton("✖️ Close", callback_data="close_message")]
        ])
        
        try:
            await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass # Same content
        await query.answer()

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route callback queries to the appropriate handler."""
    data = update.callback_query.data
    if data.startswith("game_"):
        await handle_game_callbacks(update, context)
    else:
        await handle_general_callbacks(update, context)
