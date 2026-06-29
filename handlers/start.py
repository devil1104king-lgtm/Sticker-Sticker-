from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.forcejoin import check_force_join
from database import get_all_categories, set_user_category, get_user_category
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    if not user:
        return

    # Check force join first
    if not await check_force_join(update, context):
        return

    # If joined, show welcome menu
    await show_welcome_menu(update, context)

async def show_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display category selection keyboard."""
    categories = await get_all_categories()
    keyboard = []
    row = []
    for i, cat in enumerate(categories):
        button = InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"category_{cat['name']}"
        )
        row.append(button)
        if len(row) == 2:  # two columns
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Add a help/info button maybe
    keyboard.append([InlineKeyboardButton("ℹ️ Help", callback_data="help")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    user = update.effective_user
    # Get current category
    current_cat = await get_user_category(user.id)
    text = (
        f"👋 Welcome {user.first_name}!\n\n"
        "Select a sticker category below. Then send any sticker to get a reply from that category.\n"
        "You can change category anytime by clicking a button.\n\n"
        f"Current category: {current_cat or 'None selected'}"
    )
    if update.callback_query:
        # Edit message if callback
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help info."""
    query = update.callback_query
    await query.answer()
    text = (
        "🤖 **Sticker Game Bot**\n\n"
        "1. Select a category using the buttons.\n"
        "2. Send any sticker to the bot.\n"
        "3. The bot will reply with a random sticker from that category.\n"
        "4. Change category anytime by clicking a button.\n\n"
        "Have fun! 😄"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]))
