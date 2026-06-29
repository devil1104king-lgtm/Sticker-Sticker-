from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def game_request_kb(challenger_id: int, challenged_id: int) -> InlineKeyboardMarkup:
    """Keyboard for accepting or declining a game."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"game_accept_{challenger_id}_{challenged_id}"),
            InlineKeyboardButton("❌ Decline", callback_data=f"game_decline_{challenger_id}_{challenged_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button_kb(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Standard back button keyboard."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=callback_data)]])

def close_button_kb() -> InlineKeyboardMarkup:
    """Standard close button keyboard."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close", callback_data="close_message")]])
  
