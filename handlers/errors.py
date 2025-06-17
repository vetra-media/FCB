"""
handlers/errors.py - Error Handling
Comprehensive error handling for the Telegram bot
"""

import logging

from telegram.ext import ContextTypes
from telegram.error import TelegramError

# =============================================================================
# Enhanced Error Handler
# =============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in the bot with user-friendly messages and comprehensive logging
    """
    logging.error(msg='Exception while handling an update:', exc_info=context.error)
    
    # Log detailed error information
    if update:
        logging.error(f"❌ ERROR CONTEXT: Update type: {type(update)}")
        if hasattr(update, 'effective_user') and update.effective_user:
            logging.error(f"❌ ERROR CONTEXT: User ID: {update.effective_user.id}")
        if hasattr(update, 'message') and update.message:
            logging.error(f"❌ ERROR CONTEXT: Message text: {getattr(update.message, 'text', 'N/A')}")
    
    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again in a moment.",
                parse_mode='HTML'
            )
        except TelegramError as telegram_error:
            logging.error(f"Could not send error message to user: {telegram_error}")