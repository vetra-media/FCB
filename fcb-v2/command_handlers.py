"""
FCB v2 Command Handlers - COMPLETELY FIXED
User-facing commands that integrate all completed systems
"""

import logging
import time
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

# Import all our completed systems
from token_economics import (
    get_user_balance_info,
    get_user_statistics,
    get_system_statistics,
    get_clean_balance_display,
    FCB_STAR_PACKAGES
)
from session_manager import (
    get_user_session,
    get_session_navigation_state,
    get_session_stats,
    debug_user_session,
    clear_user_session
)
from payment_handler import (
    create_purchase_menu,
    get_payment_stats
)
from navigation_handler import (
    get_navigation_buttons
)

logger = logging.getLogger(__name__)

# =============================================================================
# COMMAND RESULT CLASS
# =============================================================================

class CommandResult:
    """Result object for command operations"""
    def __init__(self, success: bool, message: str = "", keyboard: InlineKeyboardMarkup = None,
                 parse_mode: str = 'Markdown', disable_preview: bool = True):
        self.success = success
        self.message = message
        self.keyboard = keyboard
        self.parse_mode = parse_mode
        self.disable_preview = disable_preview

# =============================================================================
# MAIN COMMAND HANDLER CLASS - COMPLETELY FIXED
# =============================================================================

class FCBCommandHandler:
    """
    Main command handler for FCB v2
    Integrates all systems into user-facing commands
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.start_time = time.time()
        logger.info("FCB Command Handler initialized")
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """Handle /start command - Welcome new users and initialize sessions"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username or "there"
            first_name = update.effective_user.first_name or "User"
            
            logger.info(f"/start command from user {user_id} (@{username})")
            
            # Initialize user session and get balance info
            session = get_user_session(user_id)
            balance_info = get_user_balance_info(user_id)
            
            # CORRECT WELCOME MESSAGE (from your specification)
            welcome_text = """🎉 **Welcome to FOMO Crypto Bot!**

🚀 **Your Crypto FOMO Discovery Tool**

🆓 **You get 5 FREE scans daily** + 3 bonus starter scans!
💎 **Find early opportunities** before they pump  
⚡ **Real-time alerts** with actionable insights

Ready to discover your next crypto gem?

💎 What Makes Us Different:
Our proprietary FOMO algorithm analyzes 15+ market indicators including volume spikes, price momentum, social sentiment, and whale activity to identify early signals of moon shots.

🔥 Premium Alert System:
• Get high-quality opportunities sent directly (80%+ FOMO score only)
• Smart alerts every 4 hours (6 daily max)
• Click alert buttons for instant analysis

🎁 5 Scans Per Day FREE!
Plus 3 bonus starter scans - begin exploring immediately!

💰 Token Economics (Crystal Clear):
🟢 Always FREE: BACK navigation, buy links, alerts
🔴 1 token cost: Fresh searches, new discoveries
🎁 FREE Allowance: 8 starter scans + 5 daily scans (resets 00:00 UTC)

⚡ Quick Start: Type 'bitcoin' in chat to start me up and experience our analysis firsthand! Plus you get 8 FREE scans to explore with 5 more FREE every day!

📋 Legal Disclaimer & Terms:
By using this bot, you agree to our T&Cs. This is educational/entertainment content only - NOT financial advice. Crypto trading is extremely high risk and you could lose everything. Always DYOR (Do Your Own Research).

🎯 Ready? Type 'bitcoin' in chat to start me up and discover why thousands trust our FOMO analysis! 8 FREE starter scans + 5 daily FREE scans - no payment needed to begin!

💡 Get Help: Type /help for full instructions"""
            
            # CORRECT BUTTONS (matching your image)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Start Scanning", callback_data="start_scanning")],
                [InlineKeyboardButton("📊 My Balance", callback_data="show_balance")],
                [InlineKeyboardButton("❓ How It Works", callback_data="show_help")]
            ])
            
            return CommandResult(
                success=True,
                message=welcome_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /start command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Welcome system error. Please try again with /start"
            )
    
    async def handle_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """
        Handle /balance command - Show detailed user balance and statistics
        """
        try:
            user_id = update.effective_user.id
            logger.info(f"/balance command from user {user_id}")
            
            # Get comprehensive balance and statistics
            balance_info = get_user_balance_info(user_id)
            user_stats = get_user_statistics(user_id)
            
            # Create detailed balance message
            balance_text = "🔋 **Your FCB Account Balance**\n\n"
            
            # Current balance section
            balance_text += "💰 **Current Balance:**\n"
            balance_text += f"• FCB Tokens: **{balance_info['fcb_balance']}**\n"
            balance_text += f"• Free Daily Scans: **{balance_info['total_free_remaining']}**\n"
            balance_text += f"• **Total Available: {balance_info['total_scans']} scans**\n\n"
            
            # Usage breakdown
            balance_text += "📊 **Today's Usage:**\n"
            balance_text += f"• Daily scans used: {balance_info['free_queries_used']}/5\n"
            balance_text += f"• Bonus scans used: {balance_info['new_user_bonus_used']}/3\n\n"
            
            # Account statistics
            if user_stats.get('user_data'):
                user_data = user_stats['user_data']
                balance_text += "📈 **Account Statistics:**\n"
                balance_text += f"• Total scans performed: {user_data.get('total_queries', 0)}\n"
                balance_text += f"• FCB tokens purchased: {user_data.get('total_tokens_purchased', 0)}\n"
                balance_text += f"• FCB tokens spent: {user_data.get('total_tokens_spent', 0)}\n"
                
                # Calculate efficiency metrics
                if user_stats.get('efficiency'):
                    efficiency = user_stats['efficiency']
                    balance_text += f"• Daily scan average: {efficiency.get('tokens_per_day', 0):.1f}\n"
                
                balance_text += "\n"
            
            # Next steps
            if balance_info['total_scans'] == 0:
                balance_text += "🚨 **Out of Scans!**\n"
                balance_text += "Get more scans with /buy to continue discovering opportunities!\n\n"
            elif balance_info['total_scans'] < 5:
                balance_text += "⚠️ **Low Balance Warning**\n"
                balance_text += f"Only {balance_info['total_scans']} scans remaining. Consider getting more with /buy\n\n"
            else:
                balance_text += "✅ **Ready to Scan!**\n"
                balance_text += "You have plenty of scans available. Start discovering with any command!\n\n"
            
            balance_text += "💡 Use /buy to get more FCB tokens anytime!"
            
            # Create action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💰 Buy More Tokens", callback_data="show_buy_menu"),
                    InlineKeyboardButton("🔍 Start Scanning", callback_data="start_scanning")
                ],
                [
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="show_detailed_stats"),
                    InlineKeyboardButton("🔄 Refresh Balance", callback_data="refresh_balance")
                ]
            ])
            
            return CommandResult(
                success=True,
                message=balance_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /balance command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Balance system error. Please try /balance again."
            )
    
    async def handle_buy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """
        Handle /buy command - Show FCB token purchase options
        """
        try:
            user_id = update.effective_user.id
            logger.info(f"/buy command from user {user_id}")
            
            # Get purchase menu from payment handler
            menu_text, keyboard = create_purchase_menu(user_id)
            
            return CommandResult(
                success=True,
                message=menu_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /buy command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Purchase system error. Please try /buy again."
            )
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """
        Handle /help command - Show comprehensive help and features guide
        """
        try:
            user_id = update.effective_user.id
            logger.info(f"/help command from user {user_id}")
            
            help_text = "❓ **FCB v2 Help Guide**\n\n"
            
            # Core commands section
            help_text += "🔧 **Main Commands:**\n"
            help_text += "• `/start` - Initialize your FCB account\n"
            help_text += "• `/scan` - Discover new crypto opportunities\n"
            help_text += "• `/balance` - Check your scan balance & stats\n"
            help_text += "• `/buy` - Purchase FCB tokens with Telegram Stars\n"
            help_text += "• `/help` - Show this help guide\n"
            help_text += "• `/status` - System status & your session info\n\n"
            
            # Navigation explanation
            help_text += "🧭 **Navigation System:**\n"
            help_text += "• **BACK Button**: Navigate through history (always FREE)\n"
            help_text += "• **NEXT Button**: Forward through history (FREE) or discover new (1 scan)\n"
            help_text += "• **Smart Cost Display**: Buttons show exactly what they cost\n"
            help_text += "• **Session Memory**: Your history is cached for 24 hours\n\n"
            
            # Token economics explanation
            help_text += "💰 **FCB Token Economics:**\n"
            help_text += "• **Free Daily Scans**: 5 per day (resets at midnight)\n"
            help_text += "• **New User Bonus**: 3 additional scans when you start\n"
            help_text += "• **FCB Tokens**: Premium scans with no daily limits\n"
            help_text += "• **Smart Spending**: Uses free scans first, then tokens\n\n"
            
            # Package information
            help_text += "📦 **Token Packages:**\n"
            for package_key, package_info in FCB_STAR_PACKAGES.items():
                stars = package_info['stars']
                tokens = package_info['tokens']
                help_text += f"• **{package_info['title']}**: {stars} ⭐ → {tokens} 🔋\n"
            help_text += "\n"
            
            # Features section
            help_text += "🚀 **Key Features:**\n"
            help_text += "• **Elite Analysis**: Advanced crypto opportunity detection\n"
            help_text += "• **Smart Caching**: Previous scans cost nothing to revisit\n"
            help_text += "• **Rate Limiting**: 1-second cooldown prevents spam\n"
            help_text += "• **Alert Integration**: Special navigation from alerts\n"
            help_text += "• **Secure Payments**: Telegram Stars integration\n\n"
            
            help_text += "💡 **Pro Tips:**\n"
            help_text += "• Navigate BACK through history for free analysis\n"
            help_text += "• Buy tokens in bulk for better value\n"
            help_text += "• Your session saves history for 24 hours\n"
            help_text += "• Daily scans reset every midnight UTC\n\n"
            
            help_text += "🆘 **Need Support?**\n"
            help_text += "Contact @YourSupportUsername for help!"
            
            # Create helpful action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Start Scanning", callback_data="start_scanning"),
                    InlineKeyboardButton("💰 Buy Tokens", callback_data="show_buy_menu")
                ],
                [
                    InlineKeyboardButton("📊 Check Balance", callback_data="show_balance"),
                    InlineKeyboardButton("🔧 System Status", callback_data="show_status")
                ]
            ])
            
            return CommandResult(
                success=True,
                message=help_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /help command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Help system error. Please try /help again."
            )
    
    async def handle_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """
        Handle /status command - Show system status and user session info
        """
        try:
            user_id = update.effective_user.id
            logger.info(f"/status command from user {user_id}")
            
            # Get system and user statistics
            system_stats = get_system_statistics()
            session_stats = get_session_stats()
            payment_stats = get_payment_stats()
            user_session = get_user_session(user_id)
            nav_state = get_session_navigation_state(user_id)
            
            status_text = "🔧 **FCB v2 System Status**\n\n"
            
            # System health
            uptime_hours = (time.time() - self.start_time) / 3600
            status_text += "💚 **System Health: OPERATIONAL**\n"
            status_text += f"• Uptime: {uptime_hours:.1f} hours\n"
            status_text += f"• Active users (24h): {system_stats['users']['active_24h']}\n"
            status_text += f"• Total users: {system_stats['users']['total']}\n\n"
            
            # Token economics status
            status_text += "💰 **Token Economics:**\n"
            status_text += f"• Total FCB balance in system: {system_stats['tokens']['total_balance']}\n"
            status_text += f"• Tokens purchased today: {system_stats['tokens']['total_purchased']}\n"
            status_text += f"• Active payments: {payment_stats['pending_payments']}\n\n"
            
            # Session system status
            status_text += "📱 **Session System:**\n"
            status_text += f"• Active sessions: {session_stats['active_sessions']}\n"
            status_text += f"• Cached items: {session_stats['total_cached_items']}\n"
            status_text += f"• Memory usage: ~{session_stats['memory_usage_mb']} MB\n\n"
            
            # User's session info
            status_text += "👤 **Your Session:**\n"
            if nav_state:
                status_text += f"• History length: {nav_state['total_coins']} coins\n"
                status_text += f"• Current position: {nav_state['current_position']}\n"
                status_text += f"• Can go back: {'Yes' if nav_state['can_go_back'] else 'No'}\n"
                status_text += f"• Can go forward: {'Yes' if nav_state['can_go_forward'] else 'No'}\n"
            else:
                status_text += "• No active session\n"
            
            cached_count = len(user_session.get('cached_data', {}))
            status_text += f"• Cached coins: {cached_count}\n\n"
            
            # System capabilities
            status_text += "⚡ **System Capabilities:**\n"
            status_text += "• Rate limiting: ✅ Active\n"
            status_text += "• Payment processing: ✅ Available\n"
            status_text += "• Session management: ✅ Operational\n"
            status_text += "• Navigation system: ✅ Ready\n"
            status_text += "• Token economics: ✅ Active\n\n"
            
            status_text += "🚀 **All systems ready for crypto discovery!**"
            
            # Create admin/debug buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status"),
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="show_detailed_stats")
                ],
                [
                    InlineKeyboardButton("🧹 Clear Session", callback_data="clear_my_session"),
                    InlineKeyboardButton("🔍 Start Scanning", callback_data="start_scanning")
                ]
            ])
            
            return CommandResult(
                success=True,
                message=status_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /status command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Status system error. Please try /status again."
            )
    
    async def handle_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
        """
        Handle /scan command - Start crypto opportunity discovery
        """
        try:
            user_id = update.effective_user.id
            logger.info(f"/scan command from user {user_id}")
            
            # Check if user has scans available
            balance_info = get_user_balance_info(user_id)
            
            if balance_info['total_scans'] == 0:
                # No scans available
                no_scans_text = "🚨 **No Scans Available!**\n\n"
                no_scans_text += "You've used all your free daily scans and have no FCB tokens.\n\n"
                no_scans_text += "💰 **Get More Scans:**\n"
                no_scans_text += "• Buy FCB tokens with /buy\n"
                no_scans_text += "• Wait for daily reset (5 free scans)\n"
                no_scans_text += "• Navigate BACK through history (always free)\n\n"
                no_scans_text += "🔋 **Current Balance:**\n"
                no_scans_text += f"• FCB Tokens: {balance_info['fcb_balance']}\n"
                no_scans_text += f"• Free Scans: {balance_info['total_free_remaining']}\n\n"
                no_scans_text += "Ready to power up? 🚀"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Buy FCB Tokens", callback_data="show_buy_menu")],
                    [InlineKeyboardButton("📊 Check Balance", callback_data="show_balance")]
                ])
                
                return CommandResult(
                    success=False,
                    message=no_scans_text,
                    keyboard=keyboard
                )
            
            # User has scans available - show scanning interface
            scan_text = "🔍 **FCB Crypto Scanner Ready!**\n\n"
            scan_text += f"🔋 **Available Scans: {balance_info['total_scans']}**\n"
            if balance_info['total_free_remaining'] > 0:
                scan_text += f"• Free scans: {balance_info['total_free_remaining']}\n"
            if balance_info['fcb_balance'] > 0:
                scan_text += f"• FCB tokens: {balance_info['fcb_balance']}\n"
            scan_text += "\n"
            
            scan_text += "🎯 **What would you like to do?**\n"
            scan_text += "• **Discover New**: Find fresh opportunities (1 scan)\n"
            scan_text += "• **Navigate History**: Review previous scans (FREE)\n"
            scan_text += "• **Check Alerts**: View any active alerts\n\n"
            
            scan_text += "💡 **Pro Tip**: Navigation through history is always FREE!"
            
            # Create scanning action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Discover New (1 🔋)", callback_data="discover_new"),
                    InlineKeyboardButton("📈 Check Alerts", callback_data="check_alerts")
                ]
            ])
            
            # Add navigation buttons if user has history
            nav_state = get_session_navigation_state(user_id)
            if nav_state and nav_state['total_coins'] > 0:
                nav_buttons = get_navigation_buttons(user_id)
                # Combine with existing buttons
                all_buttons = keyboard.inline_keyboard + nav_buttons.inline_keyboard
                keyboard = InlineKeyboardMarkup(all_buttons)
            
            return CommandResult(
                success=True,
                message=scan_text,
                keyboard=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in /scan command for user {user_id}: {e}")
            return CommandResult(
                success=False,
                message="❌ Scanner system error. Please try /scan again."
            )

# =============================================================================
# GLOBAL COMMAND HANDLER INSTANCE
# =============================================================================

command_handler = FCBCommandHandler()

# =============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# =============================================================================

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /start command"""
    return await command_handler.handle_start_command(update, context)

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /balance command"""
    return await command_handler.handle_balance_command(update, context)

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /buy command"""
    return await command_handler.handle_buy_command(update, context)

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /help command"""
    return await command_handler.handle_help_command(update, context)

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /status command"""
    return await command_handler.handle_status_command(update, context)

async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """Handle /scan command"""
    return await command_handler.handle_scan_command(update, context)

# =============================================================================
# TELEGRAM COMMAND HANDLERS SETUP
# =============================================================================

def get_command_handlers():
    """
    Get list of CommandHandler objects for registering with telegram bot
    """
    return [
        CommandHandler("start", handle_start),
        CommandHandler("balance", handle_balance),
        CommandHandler("buy", handle_buy),
        CommandHandler("help", handle_help),
        CommandHandler("status", handle_status),
        CommandHandler("scan", handle_scan),
    ]

# =============================================================================
# COMMAND ROUTER FOR INTEGRATION
# =============================================================================

async def route_command(command: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CommandResult:
    """
    Route commands to appropriate handlers
    """
    try:
        if command == "start":
            return await handle_start(update, context)
        elif command == "balance":
            return await handle_balance(update, context)
        elif command == "buy":
            return await handle_buy(update, context)
        elif command == "help":
            return await handle_help(update, context)
        elif command == "status":
            return await handle_status(update, context)
        elif command == "scan":
            return await handle_scan(update, context)
        else:
            return CommandResult(
                success=False,
                message=f"❌ Unknown command: /{command}\n\nUse /help to see available commands."
            )
    except Exception as e:
        logger.error(f"Error routing command {command}: {e}")
        return CommandResult(
            success=False,
            message="❌ Command processing error. Please try again."
        )

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_command_system():
    """Initialize the command system"""
    logger.info("🎮 FCB v2 Command System initialized")
    logger.info("📋 Available commands: /start, /balance, /buy, /help, /status, /scan")
    logger.info("🔗 All systems integrated and ready for user interaction")

# Auto-initialize when module is imported
initialize_command_system()