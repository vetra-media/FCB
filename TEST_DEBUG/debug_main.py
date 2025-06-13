# Add these imports to your main bot file
from telegram.ext import CommandHandler, CallbackQueryHandler
from handlers import start_command, test_command, status_command, handle_callback_query

# Add these handler registrations to your application setup
def setup_handlers(application):
    """Register all command and callback handlers"""
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Callback query handler for interactive buttons
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    return application

# Example usage in your main function:
# application = setup_handlers(application)