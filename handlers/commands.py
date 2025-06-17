"""
handlers/commands.py - Core Command Handlers
Essential bot commands: start, help, balance, purchase commands
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Import from other modules
from database import (
    get_user_balance, get_user_balance_detailed,
    FREE_QUERIES_PER_DAY, NEW_USER_BONUS
)
from formatters import (
    format_purchase_options_message, build_purchase_keyboard,
    format_balance_message
)
from scanner import add_user_to_notifications
from campaign_manager import campaign_manager, format_campaign_welcome

# Import from core utilities
from .core import get_user_balance_info, get_clean_balance_display

# =============================================================================
# ENHANCED START COMMAND WITH CAMPAIGN TRACKING
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with campaign tracking"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logging.info(f"🔍 START DEBUG: User {username} (ID: {user_id}) triggered /start command")
    
    # CAMPAIGN TRACKING: Process campaign tracking
    campaign_data = campaign_manager.process_start_command(user_id, context.args)
    
    # Log campaign attribution
    if campaign_data['is_campaign_user']:
        logging.info(f"📈 User {user_id} from campaign: {campaign_data['campaign_code']} (source: {campaign_data['source']})")
    
    # Subscribe user to notifications
    add_user_to_notifications(user_id)
    logging.info(f"User {username} (ID: {user_id}) subscribed to opportunity alerts")
    
    # Format welcome message with campaign awareness
    welcome_text = format_campaign_welcome(campaign_data)
    
    # Add the rest of the welcome content
    welcome_text += f"""

💎 <b>What Makes Us Different:</b>
Our proprietary FOMO algorithm analyzes 15+ market indicators including volume spikes, price momentum, social sentiment, and whale activity to identify early signals of moon shots.

🔥 <b>Premium Alert System:</b>
• Get high-quality opportunities sent directly (80%+ FOMO score only)
• Smart alerts every 4 hours (6 daily max)
• Click alert buttons for instant analysis

🎁 <b>5 Scans Per Day FREE!</b>
Plus 3 bonus starter scans - begin exploring immediately!

💰 <b>Token Economics (Crystal Clear):</b>
🟢 <b>Always FREE:</b> BACK navigation, buy links, alerts
🔴 <b>1 token cost:</b> Fresh searches, new discoveries
🎁 <b>FREE Allowance:</b> 8 starter scans + 5 daily scans (resets 00:00 UTC)

⚡ <b>Quick Start:</b> Type '<b>bitcoin</b>' in chat to start me up and experience our analysis firsthand! <b>Plus you get 8 FREE scans to explore</b> with 5 more FREE every day!

📋 <b>Legal Disclaimer & Terms:</b>
By using this bot, you agree to our T&Cs. This is educational/entertainment content only - NOT financial advice. Crypto trading is extremely high risk and you could lose everything. Always DYOR (Do Your Own Research).

🎯 <b>Ready?</b> Type '<b>bitcoin</b>' in chat to start me up and discover why thousands trust our FOMO analysis! <b>8 FREE starter scans + 5 daily FREE scans</b> - no payment needed to begin!

💡 <b>Get Help:</b> Type /help for full instructions"""
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔍 Start Scanning", callback_data="start_scan")],
        [InlineKeyboardButton("📊 My Balance", callback_data="check_balance")], 
        [InlineKeyboardButton("❓ How It Works", callback_data="show_help")]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    logging.info(f"✅ START: Successfully sent welcome message to {username}")

# =============================================================================
# HELP AND INFORMATION COMMANDS
# =============================================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 HELP DEBUG: User {username} (ID: {user_id}) triggered /help command")
        
        message = f"""💡 <b>How FOMO Bot Works & Instructions</b>

🎯 <b>Our FOMO Score System:</b>
We analyze 15+ market indicators and deliver a simple FOMO score that reflects extensive research underneath. Deeper analysis takes place on exchange networks.

📊 <b>FOMO Scores Explained:</b>
• 85%+ = 🚀 Very high probability opportunity
• 70%+ = ⚡ High probability opportunity  
• 55%+ = 📈 Good opportunity
• 40%+ = 👀 Moderate opportunity
• - Below 40% = 😴 Low opportunity

🔥 <b>Alert System:</b>
• Get opportunities sent directly to you
• Only 80%+ FOMO score coins trigger alerts
• Click alert buttons to explore further
• 6 alerts max per day (every 4 hours)

🎯 <b>How to Use:</b>
• Type any coin name (like "bitcoin", "pepe") → Costs 1 token
• Click 👉 NEXT for new opportunities → Costs 1 token
• Click ⬅️ BACK to revisit previous coins → FREE
• Click 💰 BUY to find purchase links → FREE
• Click 🤖 TOP UP to buy more scans → FREE

💰 <b>Token Economics:</b>
• 🔴 Costs 1 token: Fresh coin data (new searches, NEXT discoveries)
• 🟢 Always FREE: Navigation through your history, buy links

💎 <b>Scans:</b>
• Free daily scans reset at 00:00 UTC
• FCB tokens never expire
• Premium users get 250+ scans per purchase

💡 <b>Commands:</b>
• `/start` - Subscribe to alerts
• `/scans` - Check remaining scan balance
• `/premium` - View premium packages
• `/support` - Contact support
• `/test` - Test notification system
• `/terms` - Terms & Conditions"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        logging.info(f"✅ HELP SUCCESS: Help message sent to {username} (ID: {user_id})")
        
    except Exception as e:
        logging.error(f"❌ HELP ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Sorry, there was an error loading the help information. Please try again or contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception as fallback_error:
            logging.error(f"❌ HELP FALLBACK ERROR: {fallback_error}")

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command - Terms & Conditions"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 TERMS DEBUG: User {username} (ID: {user_id}) triggered /terms command")
        
        message = """📄 <b>Terms & Conditions - FOMO Crypto Bot</b>

🤖 <b>Service Description</b>
• FOMO Crypto Bot provides FOMO scores for cryptocurrencies
• Premium packages: 100/250/500/1000 scans
• Scores based on extensive research & analysis

⚖️ <b>LEGAL DISCLAIMER:</b>
This bot is for educational and entertainment purposes ONLY. Nothing here constitutes financial, investment, or trading advice.

🚨 <b>HIGH RISK WARNING:</b>
• Cryptocurrency trading is EXTREMELY HIGH RISK
• You could lose ALL your money
• Past performance ≠ future results
• Markets are volatile and unpredictable

💡 <b>Our FOMO Algorithm:</b>
Our proprietary system analyzes market indicators for educational purposes only. High FOMO scores do NOT guarantee profits or predict price movements.

👤 <b>User Responsibilities:</b>
• Must be 18+ and legally able to trade crypto
• ALWAYS Do Your Own Research (DYOR)
• Only invest what you can afford to lose
• Verify all information independently
• We are NOT financial advisors

⚖️ <b>Usage Terms</b>
• For informational purposes only
• Not financial advice - DYOR
• FOMO scores are analysis tools, not guarantees
• Deeper research recommended on exchanges

💳 <b>Payment & Refunds</b>
• All sales final - no refunds
• Scans expire after 30 days
• Contact @fomocryptopings for support

📊 <b>Data & Privacy:</b>
• We store usage data for bot functionality
• No personal financial information stored
• Data used to improve user experience

⚖️ <b>Limitation of Liability:</b>
FOMO Crypto Bot, its creators, and affiliates are NOT liable for any financial losses, damages, or consequences from using this service.

<b>By using this bot, you acknowledge reading and agreeing to these terms.</b>

📞 <b>Contact:</b> @fomocryptopings

<i>Last updated: 2025</i>"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        logging.info(f"✅ TERMS: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ TERMS ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error loading terms. Please contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command - Contact support"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 SUPPORT DEBUG: User {username} (ID: {user_id}) triggered /support command")
        
        message = """📞 <b>Contact Support</b>

🤖 <b>FOMO Crypto Bot Support</b>

💬 <b>Get Help:</b>
Contact us directly: @fomocryptopings

🕒 <b>Support Hours:</b>
Available: 00:00 UTC Daily

❓ <b>Common Questions:</b>
• Scan balance issues
• Payment problems  
• Technical difficulties
• Feature requests

💡 <b>Before Contacting:</b>
• Try /help for instructions
• Check /scans for balance
• Use /test to verify alerts work

📧 <b>What to Include:</b>
• Your username
• Description of the issue
• Screenshots if helpful

We typically respond within 24 hours!"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Contact @fomocryptopings", url="https://t.me/fomocryptopings")],
            [InlineKeyboardButton("📋 View Help", callback_data="show_help")]
        ])
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
        logging.info(f"✅ SUPPORT: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ SUPPORT ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error loading support info. Contact @fomocryptopings directly for help.",
                parse_mode='HTML'
            )
        except Exception:
            pass

# =============================================================================
# BALANCE AND SCAN COMMANDS
# =============================================================================

async def scans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scans command - Check remaining scan balance"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 SCANS DEBUG: User {username} (ID: {user_id}) triggered /scans command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        fcb_balance = user_balance_info.get('fcb_balance', 0)
        total_free_remaining = user_balance_info.get('total_free_remaining', 0)
        total_scans = total_free_remaining + fcb_balance
        
        message = f"""🎯 <b>Your Scan Balance</b>

📊 <b>Available Scans:</b> {total_scans}
🎁 <b>Free Scans:</b> {total_free_remaining}
💎 <b>FCB Tokens:</b> {fcb_balance}

💰 <b>How Scans Work:</b>
🟢 <b>Always FREE:</b> ⬅️ BACK navigation, 💰 buy links
🔴 <b>1 scan each:</b> New coin searches, 👉 NEXT discoveries

⏰ <b>Daily Reset:</b> Free scans reset at 00:00 UTC

Need more scans? Use /premium to view packages!"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Get More Scans", callback_data="buy_starter")],
            [InlineKeyboardButton("📊 Full Balance Details", callback_data="check_balance")]
        ])
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
        logging.info(f"✅ SCANS: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ SCANS ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error checking balance. Please try again or contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - Show detailed balance"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 BALANCE DEBUG: User {username} (ID: {user_id}) triggered /balance command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        try:
            base_message = format_balance_message(user_balance_info, conversion_hooks=True)
        except ImportError as import_error:
            logging.warning(f"Import error in balance_command: {import_error}")
            # Fallback message
            fcb_balance = user_balance_info.get('fcb_balance', 0)
            total_free_remaining = user_balance_info.get('total_free_remaining', 0)
            base_message = f"""📊 <b>Your Balance</b>

🎯 <b>Scans Available:</b> {total_free_remaining}
💎 <b>FCB Tokens:</b> {fcb_balance}"""
        
        economics_info = f"""

💰 <b>Token Usage:</b>
🔴 <b>Costs 1 token:</b> New coin searches, NEXT discoveries
🟢 <b>Always FREE:</b> BACK navigation, buy coin links

💡 <b>Smart Usage Tips:</b>
• Use ⬅️ BACK to revisit coins without cost
• Alerts give you premium coins to explore freely
• NEXT finds fresh opportunities (costs 1 token)"""
        
        full_message = base_message + economics_info
        await update.message.reply_text(full_message, parse_mode='HTML')
        logging.info(f"✅ BALANCE: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ BALANCE ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error checking balance. Please try again or contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

async def debug_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check detailed balance information"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 DEBUG_BALANCE: User {username} (ID: {user_id}) triggered /debug command")
        
        balance_info = get_user_balance_detailed(user_id)
        
        if balance_info:
            message = f"""🔍 <b>Debug Balance Info</b>

👤 <b>User ID:</b> {user_id}
💎 <b>FCB Balance:</b> {balance_info['fcb_balance']}
🎯 <b>Free Queries Used:</b> {balance_info['free_queries_used']}/{FREE_QUERIES_PER_DAY}
🎁 <b>Bonus Used:</b> {balance_info['new_user_bonus_used']}/{NEW_USER_BONUS}
✅ <b>Bonus Received:</b> {balance_info['has_received_bonus']}
📊 <b>Total Queries:</b> {balance_info['total_queries']}
📅 <b>Created:</b> {balance_info['created_at']}
💰 <b>First Purchase:</b> {balance_info['first_purchase_date'] or 'None'}

🎯 <b>Available Scans:</b> {balance_info['total_free_remaining']} free + {balance_info['fcb_balance']} tokens

🔧 <b>Session Debug:</b> Check logs for session details"""
        else:
            message = "❌ Could not retrieve balance information."
        
        await update.message.reply_text(message, parse_mode='HTML')
        logging.info(f"✅ DEBUG_BALANCE: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ DEBUG_BALANCE ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error retrieving debug information. Please contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

# =============================================================================
# PURCHASE COMMANDS
# =============================================================================

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command - View premium packages"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 PREMIUM DEBUG: User {username} (ID: {user_id}) triggered /premium command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        try:
            message = format_purchase_options_message(user_balance_info)
            keyboard = build_purchase_keyboard()
        except ImportError as import_error:
            logging.warning(f"Import error in premium_command: {import_error}")
            # Fallback message
            message = f"""⭐ <b>Get Premium Scan Packages!</b>

<b>💫 Pay with Telegram Stars:</b>
⭐ <b>Starter</b> - 100 Stars → 100 scans
🔥 <b>Premium</b> - 250 Stars → 250 scans <b>(MOST POPULAR)</b>
⭐ <b>Pro</b> - 500 Stars → 500 scans
⭐ <b>Elite</b> - 1,000 Stars → 1,000 scans

Contact @fomocryptopings for help!"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Get 250 Scans", callback_data="buy_premium")]
            ])
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
        logging.info(f"✅ PREMIUM: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ PREMIUM ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error loading premium options. Please contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command - Show FCB token purchase options"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 BUY DEBUG: User {username} (ID: {user_id}) triggered /buy command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        try:
            message = format_purchase_options_message(user_balance_info)
            keyboard = build_purchase_keyboard()
        except ImportError as import_error:
            logging.warning(f"Import error in buy_command: {import_error}")
            # Fallback message
            message = f"""⭐ <b>Get Premium Scan Packages!</b>

<b>💫 Pay with Telegram Stars:</b>
⭐ <b>Starter</b> - 100 Stars → 100 scans
🔥 <b>Premium</b> - 250 Stars → 250 scans <b>(MOST POPULAR)</b>
⭐ <b>Pro</b> - 500 Stars → 500 scans
⭐ <b>Elite</b> - 1,000 Stars → 1,000 scans"""
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Get 250 Scans", callback_data="buy_premium")]
            ])
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
        logging.info(f"✅ BUY: Successfully sent to {username}")
        
    except Exception as e:
        logging.error(f"❌ BUY ERROR: Failed for user {update.effective_user.id}: {e}")
        try:
            await update.message.reply_text(
                "❌ Error loading purchase options. Please contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
        except Exception:
            pass

# =============================================================================
# COMMAND REGISTRY
# =============================================================================

CORE_COMMANDS = {
    'start': start_command,
    'help': help_command,
    'terms': terms_command,
    'scans': scans_command,
    'premium': premium_command,
    'support': support_command,
    'buy': buy_command,
    'balance': balance_command,
    'debug': debug_balance_command
}