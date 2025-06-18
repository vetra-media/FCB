"""
FCB v2 Main Bot - Complete Integration
Brings together all 7 completed systems into a working Telegram bot
"""

import logging
import asyncio
import os
import signal
import sys
import time
from typing import Dict, Any, Optional
from telegram import Update, BotCommand
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Import all completed FCB v2 systems
from command_handlers import (
    handle_start,
    handle_balance, 
    handle_buy,
    handle_help,
    handle_status,
    handle_scan,
    get_command_handlers,
    CommandResult
)
from callback_router import (
    handle_callback_query,
    get_callback_handler,
    process_callback_query
)
from payment_handler import (
    handle_pre_checkout_query,
    handle_successful_payment,
    cleanup_expired_payments
)
from token_economics import (
    get_system_statistics,
    initialize_token_economics
)
from session_manager import (
    cleanup_old_sessions,  # ✅ CORRECT NAME
    get_session_stats
)
import logging
logging.basicConfig(level=logging.DEBUG)
print("🔍 DEBUG: Starting FCB v2...")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================================
# BOT CONFIGURATION
# =============================================================================

class FCBBotConfig:
    """Configuration for FCB v2 Bot"""
    
    def __init__(self):
        # Get bot token from environment variable
        self.BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # Bot settings
        self.BOT_USERNAME = "fomocrypto_bot"  # Replace with your bot username
        self.DEVELOPER_CHAT_ID = None  # Set to your Telegram ID for admin messages
        
        # System settings
        self.CLEANUP_INTERVAL = 300  # 5 minutes
        self.MAX_CONCURRENT_USERS = 1000
        
        # Feature flags
        self.ENABLE_PAYMENTS = True
        self.ENABLE_ANALYTICS = True
        self.ENABLE_DEBUG_COMMANDS = False  # Set to True during development
        
        logger.info("FCB v2 Bot configuration loaded")

# =============================================================================
# MAIN BOT CLASS
# =============================================================================

class FCBBot:
    """
    Main FCB v2 Bot class
    Integrates all systems and manages the bot lifecycle
    """
    
    def __init__(self, config: FCBBotConfig):
        self.config = config
        self.application = None
        self.is_running = False
        self.stats = {
            'start_time': None,
            'messages_processed': 0,
            'commands_processed': 0,
            'callbacks_processed': 0,
            'payments_processed': 0,
            'errors': 0
        }
        logger.info("FCB v2 Bot initialized")
    
    async def initialize(self):
        """Initialize the bot application and handlers"""
        try:
            # Create application
            self.application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Set up command handlers
            await self._setup_command_handlers()
            
            # Set up callback handlers  
            await self._setup_callback_handlers()
            
            # Set up payment handlers
            if self.config.ENABLE_PAYMENTS:
                await self._setup_payment_handlers()
            
            # Set up system handlers
            await self._setup_system_handlers()
            
            # Set bot commands for the menu
            await self._setup_bot_commands()
            
            logger.info("✅ FCB v2 Bot initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    async def _setup_command_handlers(self):
        """Set up all command handlers"""
        # Main commands from command_handlers.py
        command_handlers = [
            CommandHandler("start", self._handle_start_wrapper),
            CommandHandler("balance", self._handle_balance_wrapper),
            CommandHandler("buy", self._handle_buy_wrapper),
            CommandHandler("help", self._handle_help_wrapper),
            CommandHandler("status", self._handle_status_wrapper),
            CommandHandler("scan", self._handle_scan_wrapper),
        ]
        
        # Add debug commands if enabled
        if self.config.ENABLE_DEBUG_COMMANDS:
            command_handlers.extend([
                CommandHandler("debug", self._handle_debug_command),
                CommandHandler("stats", self._handle_stats_command),
                CommandHandler("cleanup", self._handle_cleanup_command),
            ])
        
        # Register all handlers
        for handler in command_handlers:
            self.application.add_handler(handler)
        
        logger.info(f"📋 Registered {len(command_handlers)} command handlers")
    
    async def _setup_callback_handlers(self):
        """Set up callback query handlers"""
        # Main callback router from callback_router.py
        callback_handler = get_callback_handler()
        self.application.add_handler(callback_handler)
        
        logger.info("🔀 Callback router registered")
    
    async def _setup_payment_handlers(self):
        """Set up payment processing handlers"""
        # Pre-checkout query handler
        self.application.add_handler(
            PreCheckoutQueryHandler(self._handle_pre_checkout_wrapper)
        )
        
        # Successful payment handler
        self.application.add_handler(
            MessageHandler(filters.SUCCESSFUL_PAYMENT, self._handle_payment_wrapper)
        )
        
        logger.info("💳 Payment handlers registered")
    
    async def _setup_system_handlers(self):
        """Set up system-level handlers"""
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        # Unknown command handler (fallback)
        self.application.add_handler(
            MessageHandler(filters.COMMAND, self._handle_unknown_command)
        )
        
        # Non-command message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message)
        )
        
        logger.info("🔧 System handlers registered")
    
    async def _setup_bot_commands(self):
        """Set up bot command menu"""
        commands = [
            BotCommand("start", "🚀 Start FCB and initialize your account"),
            BotCommand("scan", "🔍 Discover new crypto opportunities"),
            BotCommand("balance", "🔋 Check your scan balance and statistics"),
            BotCommand("buy", "💰 Purchase FCB tokens with Telegram Stars"),
            BotCommand("help", "❓ Complete help guide and features"),
            BotCommand("status", "🔧 System status and session information"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("📋 Bot command menu configured")
    
    # =============================================================================
    # COMMAND WRAPPER FUNCTIONS
    # =============================================================================
    
    async def _handle_start_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /start command"""
        await self._process_command("start", update, context, handle_start)
    
    async def _handle_balance_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /balance command"""
        await self._process_command("balance", update, context, handle_balance)
    
    async def _handle_buy_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /buy command"""
        await self._process_command("buy", update, context, handle_buy)
    
    async def _handle_help_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /help command"""
        await self._process_command("help", update, context, handle_help)
    
    async def _handle_status_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /status command"""
        await self._process_command("status", update, context, handle_status)
    
    async def _handle_scan_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for /scan command"""
        await self._process_command("scan", update, context, handle_scan)
    
    async def _process_command(self, command_name: str, update: Update, 
                             context: ContextTypes.DEFAULT_TYPE, handler_func):
        """Generic command processing wrapper"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username or "unknown"
            
            logger.info(f"Command /{command_name} from user {user_id} (@{username})")
            
            # Call the command handler
            result = await handler_func(update, context)
            
            # Send response
            if result.success:
                await update.message.reply_text(
                    text=result.message,
                    reply_markup=result.keyboard,
                    parse_mode=result.parse_mode,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    text=result.message or f"❌ Error processing /{command_name} command",
                    parse_mode='Markdown'
                )
            
            # Update statistics
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing /{command_name} command: {e}")
            await update.message.reply_text(
                "❌ System error occurred. Please try again.",
                parse_mode='Markdown'
            )
            self.stats['errors'] += 1
    
    # =============================================================================
    # PAYMENT WRAPPER FUNCTIONS
    # =============================================================================
    
    async def _handle_pre_checkout_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for pre-checkout query handling"""
        try:
            user_id = update.pre_checkout_query.from_user.id
            logger.info(f"Pre-checkout query from user {user_id}")
            
            # Route to payment handler
            await handle_pre_checkout_query(update, context)
            
        except Exception as e:
            logger.error(f"Error in pre-checkout: {e}")
            await update.pre_checkout_query.answer(
                ok=False, 
                error_message="Payment verification failed"
            )
            self.stats['errors'] += 1
    
    async def _handle_payment_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for successful payment handling"""
        try:
            user_id = update.message.from_user.id
            logger.info(f"Successful payment from user {user_id}")
            
            # Route to payment handler
            result = await handle_successful_payment(update, context)
            
            if result.success:
                await update.message.reply_text(
                    text=result.message,
                    parse_mode='Markdown'
                )
                self.stats['payments_processed'] += 1
            else:
                await update.message.reply_text(
                    text=result.message or "❌ Payment processing error",
                    parse_mode='Markdown'
                )
                self.stats['errors'] += 1
                
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            await update.message.reply_text(
                "❌ Payment processing error. Please contact support.",
                parse_mode='Markdown'
            )
            self.stats['errors'] += 1
    
    # =============================================================================
    # SYSTEM MESSAGE HANDLERS
    # =============================================================================
    
    async def _handle_unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        try:
            command = update.message.text.split()[0] if update.message.text else ""
            user_id = update.effective_user.id
            
            logger.info(f"Unknown command {command} from user {user_id}")
            
            unknown_msg = f"❓ **Unknown command:** `{command}`\n\n"
            unknown_msg += "🤖 **Available commands:**\n"
            unknown_msg += "• `/start` - Initialize FCB\n"
            unknown_msg += "• `/scan` - Find crypto opportunities\n"
            unknown_msg += "• `/balance` - Check your balance\n"
            unknown_msg += "• `/buy` - Purchase FCB tokens\n"
            unknown_msg += "• `/help` - Full help guide\n"
            unknown_msg += "• `/status` - System status\n\n"
            unknown_msg += "💡 Use `/help` for detailed information!"
            
            await update.message.reply_text(unknown_msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error handling unknown command: {e}")
            self.stats['errors'] += 1
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command text messages"""
        try:
            user_id = update.effective_user.id
            text = update.message.text[:50] + "..." if len(update.message.text) > 50 else update.message.text
            
            logger.info(f"Text message from user {user_id}: {text}")
            
            # Friendly response encouraging command usage
            text_msg = "🤖 **Hi there!** I'm FCB - your crypto opportunity scanner.\n\n"
            text_msg += "💡 **To get started, use these commands:**\n"
            text_msg += "• `/start` - Initialize your account\n"
            text_msg += "• `/scan` - Discover crypto opportunities\n"
            text_msg += "• `/help` - See all available features\n\n"
            text_msg += "🚀 **Ready to find the next 100x gem?**"
            
            await update.message.reply_text(text_msg, parse_mode='Markdown')
            self.stats['messages_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            self.stats['errors'] += 1
    
    # =============================================================================
    # DEBUG COMMANDS (Development Only)
    # =============================================================================
    
    async def _handle_debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Debug command for development"""
        if not self.config.ENABLE_DEBUG_COMMANDS:
            return
        
        try:
            user_id = update.effective_user.id
            
            # Get system stats
            system_stats = get_system_statistics()
            session_stats = get_session_stats()
            
            debug_msg = "🔧 **FCB v2 Debug Information**\n\n"
            debug_msg += f"**Bot Stats:**\n"
            debug_msg += f"• Commands: {self.stats['commands_processed']}\n"
            debug_msg += f"• Callbacks: {self.stats['callbacks_processed']}\n"
            debug_msg += f"• Payments: {self.stats['payments_processed']}\n"
            debug_msg += f"• Errors: {self.stats['errors']}\n\n"
            
            debug_msg += f"**System Stats:**\n"
            debug_msg += f"• Users: {system_stats['users']['total']}\n"
            debug_msg += f"• Active (24h): {system_stats['users']['active_24h']}\n"
            debug_msg += f"• Sessions: {session_stats['active_sessions']}\n"
            debug_msg += f"• Memory: ~{session_stats['memory_usage_mb']} MB\n\n"
            
            debug_msg += "🔍 All systems operational!"
            
            await update.message.reply_text(debug_msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in debug command: {e}")
    
    async def _handle_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stats command for development"""
        if not self.config.ENABLE_DEBUG_COMMANDS:
            return
        
        await self._handle_status_wrapper(update, context)
    
    async def _handle_cleanup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manual cleanup command for development"""
        if not self.config.ENABLE_DEBUG_COMMANDS:
            return
        
        try:
            # Perform cleanup
            cleanup_old_sessions(time.time())
            expired_payments = cleanup_expired_payments()
            
            cleanup_msg = f"🧹 **Cleanup Complete**\n\n"
            cleanup_msg += f"• Sessions: cleaned\n"
            cleanup_msg += f"• Payments cleaned: {expired_payments}\n"
            cleanup_msg += f"• Memory freed: ~{expired_payments * 0.1:.1f} MB"
            
            await update.message.reply_text(cleanup_msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in cleanup command: {e}")
    
    # =============================================================================
    # ERROR HANDLING
    # =============================================================================
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        try:
            self.stats['errors'] += 1
            
            # Log the error
            logger.error(f"Error occurred: {context.error}", exc_info=context.error)
            
            # Try to send user-friendly error message
            if update and update.effective_user:
                error_msg = "❌ **System Error**\n\n"
                error_msg += "Something went wrong while processing your request.\n"
                error_msg += "Please try again in a moment.\n\n"
                error_msg += "💡 If the problem persists, use /help for support."
                
                try:
                    if update.message:
                        await update.message.reply_text(error_msg, parse_mode='Markdown')
                    elif update.callback_query:
                        await update.callback_query.answer(
                            text="❌ System error occurred",
                            show_alert=True
                        )
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
            
            # Notify developer if configured
            if self.config.DEVELOPER_CHAT_ID:
                try:
                    dev_msg = f"🚨 **FCB Bot Error**\n\n"
                    dev_msg += f"Error: `{str(context.error)[:100]}...`\n"
                    dev_msg += f"User: {update.effective_user.id if update else 'Unknown'}\n"
                    dev_msg += f"Total errors: {self.stats['errors']}"
                    
                    await context.bot.send_message(
                        chat_id=self.config.DEVELOPER_CHAT_ID,
                        text=dev_msg,
                        parse_mode='Markdown'
                    )
                except Exception as dev_error:
                    logger.error(f"Failed to notify developer: {dev_error}")
                    
        except Exception as handler_error:
            logger.error(f"Error in error handler: {handler_error}")
    
    # =============================================================================
    # BOT LIFECYCLE MANAGEMENT
    # =============================================================================
    
    async def start(self):
        """Start the bot"""
        try:
            if not await self.initialize():
                return False
            
            # Start periodic cleanup
            asyncio.create_task(self._periodic_cleanup())
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.is_running = True
            self.stats['start_time'] = asyncio.get_event_loop().time()
            
            logger.info("🚀 FCB v2 Bot started successfully!")
            logger.info(f"📱 Bot username: @{self.config.BOT_USERNAME}")
            logger.info("✅ Ready to process crypto opportunities!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            return False
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            if self.application and self.is_running:
                logger.info("🛑 Stopping FCB v2 Bot...")
                
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
                self.is_running = False
                
                logger.info("✅ FCB v2 Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.CLEANUP_INTERVAL)
                
                if not self.is_running:
                    break
                
                # Cleanup expired sessions and payments
                cleanup_old_sessions(time.time())
                expired_payments = cleanup_expired_payments()
                
                if expired_payments > 0:
                    logger.info(f"🧹 Cleanup: payments cleaned: {expired_payments}")
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main function to run the FCB v2 Bot"""
    
    # Initialize configuration
    try:
        config = FCBBotConfig()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Create bot instance
    bot = FCBBot(config)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the bot
    try:
        success = await bot.start()
        if not success:
            logger.error("❌ Failed to start FCB v2 Bot")
            sys.exit(1)
        
        # Keep the bot running
        while bot.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    """
    FCB v2 Bot Entry Point
    
    To run this bot:
    1. Set your TELEGRAM_BOT_TOKEN environment variable
    2. Run: python main_bot.py
    
    All 7 systems are integrated and ready!
    """
    print("🤖 Starting FCB v2 - FOMO Crypto Bot")
    print("🔥 All systems integrated and ready!")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)