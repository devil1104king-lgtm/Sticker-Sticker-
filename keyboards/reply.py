from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Generate main menu reply keyboard."""
    keyboard = [
        [KeyboardButton("🎮 Challenge"), KeyboardButton("👤 Profile")],
        [KeyboardButton("🏆 Leaderboard"), KeyboardButton("🎁 Daily Reward")],
        [KeyboardButton("🔗 Referral")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
  
