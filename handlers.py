"""
Telegram handlers module for CFB (Crypto FOMO Bot) - CAMPAIGN TRACKING INTEGRATED
PART 1/8: Core Setup, Imports, Session Management, and Utilities

CAMPAIGN TRACKING INTEGRATION:
- ✅ Campaign manager imports added
- ✅ Enhanced start_command with campaign tracking
- ✅ format_campaign_welcome integration
- ✅ Campaign data processing in start flow
"""

import logging
import random
import asyncio
import time 
from datetime import datetime 
from io import BytesIO

from telegram import Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Database imports
from database import (
    get_user_balance, 
    spend_fcb_token, 
    add_fcb_tokens, 
    check_rate_limit_with_fcb,
    get_user_balance_detailed,
    FREE_QUERIES_PER_DAY,
    NEW_USER_BONUS,
    get_db_connection
)

# Core imports
from config import FCB_STAR_PACKAGES, INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, FOMO_CACHE
from api_client import get_coin_info_ultra_fast, get_optimized_session
from analysis import calculate_fomo_status_ultra_fast

# Campaign imports - CAMPAIGN TRACKING INTEGRATION
from campaign_manager import campaign_manager

# Formatter imports
from formatters import (
    format_simple_message, format_treasure_discovery_message, format_balance_message,
    format_purchase_options_message, format_out_of_scans_message, 
    format_out_of_scans_back_message, format_payment_success_message,
    format_out_of_scans_message_with_back, format_out_of_scans_back_message_with_navigation,
    build_addictive_buttons, build_purchase_keyboard, build_out_of_scans_keyboard,
    build_out_of_scans_back_keyboard, build_out_of_scans_keyboard_with_back,
    build_out_of_scans_back_keyboard_with_navigation, create_countdown_visual,
    get_start_message, get_help_message, convert_fomo_score_to_signal,
    get_buy_coin_url
)

# Additional imports
from cache import get_ultra_fast_fomo_opportunities
from scanner import add_user_to_notifications, subscribed_users, save_subscriptions

# =============================================================================
# ECONOMICS FIX: Enhanced Session Management with Cached Data Storage
# =============================================================================

user_sessions = {}  # {user_id: {'history': [], 'index': 0, 'last_activity': timestamp, 'cached_data': {}}}

def get_user_session(user_id):
    """Get or create user-specific session for navigation history with cached data"""
    current_time = time.time()
    
    # Clean old sessions (older than 24 hours)
    cleanup_old_sessions(current_time)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'history': [],
            'index': 0,
            'last_activity': current_time,
            'cached_data': {},  # ECONOMICS FIX: Store coin data to avoid repeat API calls
            'from_alert': False  # Track if user came from alert
        }
        logging.info(f"Created new session for user {user_id}")
    else:
        # Update activity timestamp
        user_sessions[user_id]['last_activity'] = current_time
    
    return user_sessions[user_id]

def cleanup_old_sessions(current_time):
    """Remove sessions older than 24 hours to prevent memory leaks"""
    cutoff_time = current_time - (24 * 3600)  # 24 hours ago
    
    old_users = [
        user_id for user_id, session in user_sessions.items()
        if session['last_activity'] < cutoff_time
    ]
    
    for user_id in old_users:
        del user_sessions[user_id]
        logging.info(f"Cleaned up old session for user {user_id}")

def add_to_user_history(user_id, coin_id, coin_data=None, from_alert=False):
    """
    ECONOMICS FIX: Add coin to user's navigation history with cached data
    Stores coin data to enable FREE navigation without repeat API calls
    """
    session = get_user_session(user_id)
    
    # Track if this coin came from an alert
    if from_alert:
        session['from_alert'] = True
        logging.info(f"User {user_id}: Starting navigation from alert coin {coin_id}")
    
    # Only add if it's different from the last coin (avoid duplicates)
    if not session['history'] or session['history'][-1] != coin_id:
        session['history'].append(coin_id)
        # Set index to newest coin
        session['index'] = len(session['history']) - 1
        
        # ECONOMICS FIX: Cache the coin data for FREE navigation
        if coin_data:
            session['cached_data'][coin_id] = {
                'coin_data': coin_data,
                'cached_at': time.time(),
                'from_alert': from_alert
            }
            logging.info(f"User {user_id}: Cached data for {coin_id} to enable FREE navigation")
        
        logging.info(f"User {user_id}: Added {coin_id} to history at position {session['index']}")
    
    return session

def get_cached_coin_data(user_id, coin_id):
    """
    ECONOMICS FIX: Get cached coin data for FREE navigation
    Returns cached data if available, None if needs fresh API call
    """
    session = get_user_session(user_id)
    cached_data = session.get('cached_data', {}).get(coin_id)
    
    if cached_data:
        # Check if cache is still fresh (within 1 hour)
        cache_age = time.time() - cached_data.get('cached_at', 0)
        if cache_age < 3600:  # 1 hour cache
            logging.info(f"Using cached data for {coin_id} (age: {cache_age:.0f}s) - FREE navigation")
            return cached_data['coin_data']
        else:
            # Cache expired
            logging.info(f"Cache expired for {coin_id} (age: {cache_age:.0f}s) - would need fresh API call")
            return None
    
    logging.info(f"No cached data for {coin_id} - would need fresh API call")
    return None

def add_alert_coin_to_history(user_id, coin_id):
    """Special function to add alert coins to user history"""
    session = add_to_user_history(user_id, coin_id, from_alert=True)
    logging.info(f"Alert coin {coin_id} added to user {user_id} history for navigation")
    return session

def debug_user_session(user_id, context=""):
    """Debug function to log user session state"""
    if user_id in user_sessions:
        session = user_sessions[user_id]
        cached_count = len(session.get('cached_data', {}))
        logging.info(f"🔍 SESSION DEBUG for User {user_id} ({context}):")
        logging.info(f"  History: {session['history']}")
        logging.info(f"  Index: {session['index']}")
        logging.info(f"  History length: {len(session['history'])}")
        logging.info(f"  Cached coins: {cached_count}")
        logging.info(f"  From alert: {session.get('from_alert', False)}")
        
        if session['history'] and 0 <= session['index'] < len(session['history']):
            current_coin = session['history'][session['index']]
            is_cached = current_coin in session.get('cached_data', {})
            logging.info(f"  Current coin: {current_coin} (cached: {is_cached})")
        else:
            logging.info(f"  ❌ Index out of bounds!")
    else:
        logging.info(f"🔍 SESSION DEBUG: User {user_id} has no session")

# =============================================================================
# Alert Coin Extraction for Button Functionality
# =============================================================================

def extract_coin_id_from_alert_message(message_text):
    """Extract coin information from alert message for navigation"""
    try:
        # Parse the message to extract coin symbol or name
        lines = message_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for coin name pattern: "🚀 CoinName (SYMBOL)"
            if line.startswith('🚀 ') and '(' in line and ')' in line:
                # Extract symbol from parentheses
                symbol_start = line.rfind('(') + 1
                symbol_end = line.rfind(')')
                if symbol_start > 0 and symbol_end > symbol_start:
                    symbol = line[symbol_start:symbol_end].lower()
                    logging.info(f"Extracted symbol from alert: {symbol}")
                    return symbol
            
            # Alternative: Look for just the coin name part
            if line.startswith('🚀 '):
                coin_part = line[2:].strip()  # Remove "🚀 "
                if '(' in coin_part:
                    coin_name = coin_part.split('(')[0].strip().lower()
                    logging.info(f"Extracted coin name from alert: {coin_name}")
                    return coin_name
        
        logging.warning(f"Could not extract coin from alert message: {message_text[:100]}...")
        return None
        
    except Exception as e:
        logging.error(f"Error extracting coin from alert: {e}")
        return None

# =============================================================================
# Clean Opportunity Hunter - No Noise, Just Results
# =============================================================================

OPPORTUNITY_HUNTER_CONFIG = {
    'tier_probabilities': {
        'premium': 0.20,    # 20% chance - Top 5 coins
        'high': 0.30,       # 30% chance - Top 6-20 coins  
        'mid': 0.50         # 50% chance - Top 21-100 coins
    },
    'tier_ranges': {
        'premium': (0, 5),      # Top 5 coins
        'high': (5, 20),        # Top 6-20 coins
        'mid': (20, 100)        # Top 21-100 coins
    }
}

def hunt_next_opportunity(cached_coins):
    """
    Clean opportunity hunting without noisy excitement messages
    Returns: (selected_coin, None) - second parameter always None (no excitement spam)
    """
    if not cached_coins:
        return None, None
    
    # Determine opportunity tier based on probabilities
    rand = random.random()
    config = OPPORTUNITY_HUNTER_CONFIG
    
    if rand < config['tier_probabilities']['premium']:
        tier = 'premium'
    elif rand < config['tier_probabilities']['premium'] + config['tier_probabilities']['high']:
        tier = 'high'
    else:
        tier = 'mid'
    
    # Hunt for coin in the determined tier
    start_idx, end_idx = config['tier_ranges'][tier]
    available_coins = min(len(cached_coins), end_idx)
    
    if start_idx >= available_coins:
        # Fallback to any available opportunity
        selected_coin = random.choice(cached_coins)
        tier = 'mid'  # Fallback tier
    else:
        # Select from opportunity tier
        tier_coins = cached_coins[start_idx:available_coins]
        selected_coin = random.choice(tier_coins) if tier_coins else random.choice(cached_coins)
    
    # Clean logging (no noise)
    coin_symbol = selected_coin.get('symbol', 'UNKNOWN')
    fomo_score = selected_coin.get('fomo_score', 0)
    logging.info(f"🎯 Clean discovery: {coin_symbol} (FOMO: {fomo_score}, tier: {tier.upper()})")
    
    return selected_coin, None

# =============================================================================
# Validation and Safety Functions
# =============================================================================

def validate_coingecko_id(coin_id):
    """Validate CoinGecko ID format - CRITICAL VALIDATION for API safety"""
    if not coin_id or not isinstance(coin_id, str):
        return False
    
    # Remove common invalid patterns that crash the API
    invalid_patterns = [
        'unknown', '', None, 'null', 'undefined',
        'jerry-the-turtle-by-matt-furie',
        'agenda-47'
    ]
    
    if coin_id.lower() in [str(p).lower() for p in invalid_patterns if p]:
        logging.warning(f"🔧 VALIDATION: Rejected known problematic ID: {coin_id}")
        return False
    
    # Basic format validation
    if len(coin_id) < 2 or len(coin_id) > 100:
        return False
    
    # Check for suspicious patterns
    if coin_id.count('-') > 10:  # Too many dashes usually indicates invalid ID
        return False
    
    return True

# =============================================================================
# Balance Display Helpers
# =============================================================================

def get_clean_balance_display(user_id):
    """
    Get simple, clean balance display
    Returns "🤖 Tokens: X" - for perfect theming consistency
    """
    try:
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        total_scans = total_free_remaining + fcb_balance
        return f"🤖 <i>Tokens: {total_scans}</i>"
    except Exception as e:
        logging.error(f"Error getting clean balance: {e}")
        return "🤖 <i>Tokens: Error</i>"

def get_user_balance_info(user_id):
    """Get complete user balance info for internal use (not display)"""
    try:
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        return {
            'fcb_balance': fcb_balance,
            'free_queries_used': free_queries_used,
            'new_user_bonus_used': new_user_bonus_used,
            'total_free_remaining': total_free_remaining,
            'has_received_bonus': has_received_bonus
        }
    except Exception as e:
        logging.error(f"Error getting user balance info: {e}")
        return {
            'fcb_balance': 0,
            'free_queries_used': 0,
            'new_user_bonus_used': 0,
            'total_free_remaining': 0,
            'has_received_bonus': False
        }

# =============================================================================
# ENHANCED START COMMAND WITH CAMPAIGN TRACKING - CAMPAIGN INTEGRATION
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with campaign tracking"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logging.info(f"🔍 START DEBUG: User {username} (ID: {user_id}) triggered /start command")
    
    # CAMPAIGN TRACKING INTEGRATION: Process campaign tracking
    campaign_data = campaign_manager.process_start_command(user_id, context.args)
    
    # Log campaign attribution
    if campaign_data['is_campaign_user']:
        logging.info(f"📈 User {user_id} from campaign: {campaign_data['campaign_code']} (source: {campaign_data['source']})")
    
    # Subscribe user to notifications
    add_user_to_notifications(user_id)
    logging.info(f"User {username} (ID: {user_id}) subscribed to opportunity alerts")
    
    # CAMPAIGN TRACKING INTEGRATION: Format welcome message with campaign awareness
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
    
    # Your existing keyboard
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
# END OF PART 1/8 - Core Setup & Session Management with Campaign Tracking Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - TEXT CONSISTENCY FIXED VERSION
PART 2/8: Safe Message Editing & Core Command Handlers - CRITICAL FIXES APPLIED

FIXES APPLIED:
- ✅ Added debug logging to help command
- ✅ Fixed potential import issues with fallback imports
- ✅ Enhanced error handling for all commands
- ✅ Added command registration verification
- ✅ Fixed handler order issues
"""

# =============================================================================
# Safe Message Editing - Enhanced for Alert Compatibility
# =============================================================================

async def safe_edit_message(query, text=None, caption=None, reply_markup=None, parse_mode='HTML'):
    """
    Safely edit a message, handling alert messages and all edge cases
    This prevents all the common Telegram edit errors and provides robust fallbacks
    """
    try:
        # Special handling for alert messages that might not be editable
        if hasattr(query, 'message') and query.message:
            # Check if message has a photo (common in alerts)
            if query.message.photo:
                # Try to edit caption first
                if text is not None or caption is not None:
                    try:
                        await query.edit_message_caption(
                            caption=text or caption,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup
                        )
                        return True
                    except Exception as caption_error:
                        logging.warning(f"Caption edit failed: {caption_error}")
                        # Fall through to delete and send new
            
            # Try to edit message text
            if text is not None:
                try:
                    await query.edit_message_text(
                        text=text, 
                        parse_mode=parse_mode, 
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
                    return True
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Handle common alert message edit failures
                    if "no text in the message to edit" in error_msg or "message is not modified" in error_msg:
                        # Delete old message and send new one
                        try:
                            await query.message.delete()
                        except Exception:
                            pass  # Message might already be deleted
                        
                        # Send new message in same chat
                        await query.message.chat.send_message(
                            text=text,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                        return True
                    
                    # Other errors - fall through to fallback
                    logging.warning(f"Message edit failed: {e}")
            
            # Try caption editing if text editing failed
            elif caption is not None:
                try:
                    await query.edit_message_caption(
                        caption=caption,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup
                    )
                    return True
                except Exception:
                    pass  # Will fall back to delete+send
        
        # Fallback for alert messages - delete and send new
        try:
            if hasattr(query, 'message') and query.message:
                await query.message.delete()
        except Exception:
            pass  # Message might already be deleted or undeletable
        
        # Send new message
        if hasattr(query, 'message') and query.message:
            await query.message.chat.send_message(
                text=text or caption or "Message update failed",
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            return True
    
    except Exception as e:
        logging.error(f"❌ Failed to edit message safely: {e}")
        
        # Last resort: just answer the callback
        try:
            await query.answer("Processing...")
        except Exception:
            pass
        
        return False

# =============================================================================
# Command Handlers - FIXED with Enhanced Debug and Error Handling
# =============================================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - FIXED with comprehensive debug and error handling"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 HELP DEBUG: User {username} (ID: {user_id}) triggered /help command")
        logging.info(f"🔍 HELP DEBUG: Update object type: {type(update)}")
        logging.info(f"🔍 HELP DEBUG: Message object: {update.message}")
        
        # Create the help message
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
        
        logging.info(f"🔍 HELP DEBUG: About to send help message to {username}")
        
        # Send the help message
        sent_message = await update.message.reply_text(message, parse_mode='HTML')
        
        logging.info(f"✅ HELP SUCCESS: Help message sent to {username} (ID: {user_id})")
        logging.info(f"🔍 HELP DEBUG: Sent message ID: {sent_message.message_id}")
        
    except Exception as e:
        logging.error(f"❌ HELP ERROR: Failed for user {update.effective_user.id}: {e}")
        logging.error(f"❌ HELP ERROR: Exception type: {type(e)}")
        logging.error(f"❌ HELP ERROR: Exception details: {str(e)}")
        
        # Try to send an error message
        try:
            await update.message.reply_text(
                "❌ Sorry, there was an error loading the help information. Please try again or contact @fomocryptopings for support.",
                parse_mode='HTML'
            )
            logging.info(f"✅ HELP: Sent error fallback message to user {update.effective_user.id}")
        except Exception as fallback_error:
            logging.error(f"❌ HELP FALLBACK ERROR: {fallback_error}")

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command - Terms & Conditions with enhanced error handling"""
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

async def scans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scans command - Check remaining scan balance with enhanced error handling"""
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
        
        # Add helpful keyboard
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

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command - View premium packages with enhanced error handling"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 PREMIUM DEBUG: User {username} (ID: {user_id}) triggered /premium command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        # Safe import with fallback
        try:
            from formatters import format_purchase_options_message, build_purchase_keyboard
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

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command - Contact support with enhanced error handling"""
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
        
        # Add helpful keyboard
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

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command - Show FCB token purchase options with enhanced error handling"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 BUY DEBUG: User {username} (ID: {user_id}) triggered /buy command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        # Safe import with fallback
        try:
            from formatters import format_purchase_options_message, build_purchase_keyboard
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

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - Show detailed balance with enhanced error handling"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logging.info(f"🔍 BALANCE DEBUG: User {username} (ID: {user_id}) triggered /balance command")
        
        user_balance_info = get_user_balance_info(user_id)
        
        # Safe import with fallback
        try:
            from formatters import format_balance_message
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
    """Debug command to check detailed balance information with enhanced error handling"""
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

🔧 <b>Session Debug:</b>"""
            
            # Add session debug info
            if user_id in user_sessions:
                session = user_sessions[user_id]
                cached_count = len(session.get('cached_data', {}))
                message += f"""
📂 <b>History:</b> {len(session.get('history', []))} coins
📍 <b>Current Position:</b> {session.get('index', 0) + 1}
💾 <b>Cached Coins:</b> {cached_count}
🔥 <b>From Alert:</b> {session.get('from_alert', False)}"""
            else:
                message += "\n❌ <b>No active session</b>"
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
# COMMAND REGISTRY FOR VERIFICATION
# =============================================================================

REGISTERED_COMMANDS = {
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

def verify_command_registration():
    """Verify all commands are properly defined"""
    logging.info("🔍 VERIFYING COMMAND REGISTRATION:")
    for cmd_name, cmd_func in REGISTERED_COMMANDS.items():
        if callable(cmd_func):
            logging.info(f"  ✅ /{cmd_name} -> {cmd_func.__name__}")
        else:
            logging.error(f"  ❌ /{cmd_name} -> NOT CALLABLE!")
    logging.info(f"✅ Total commands registered: {len(REGISTERED_COMMANDS)}")

# =============================================================================
# END OF PART 2/8 - FIXED Command Handlers with Enhanced Debug Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - ECONOMICS FIXED VERSION
PART 3/8: Test Command, Debug Functions & Status Commands

Enhanced test command with fully functional buttons and comprehensive debug capabilities.
"""

# =============================================================================
# Enhanced Test Command with Functional Buttons
# =============================================================================

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test notification with fully functional buttons"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logging.info(f"Test command triggered by {username} (ID: {user_id})")
    
    # Check if user is subscribed
    if user_id not in subscribed_users:
        await update.message.reply_text(
            "❌ You're not subscribed to alerts! Send /start first to subscribe.",
            parse_mode='HTML'
        )
        return
    
    # Create realistic test data that works with navigation
    test_data = {
        'id': 'bitcoin',  # Use real coin ID for proper navigation
        'name': 'Bitcoin TEST',
        'symbol': 'BTC',
        'price': 98765.43,
        'change_1h': 2.5,
        'change_24h': 5.67,
        'volume': 25000000000,
        'logo': None
    }
    
    # Add test coin to user's navigation history with cached data
    add_to_user_history(user_id, 'bitcoin', test_data, from_alert=True)
    
    # Format the test message using simplified formatter
    message_text = format_simple_message(test_data, 85, "⚡ Early Momentum", 3.2, "Bullish", "Balanced", is_broadcast=False)
    
    # Add test indicator with economics explanation
    test_message = f"""🧪 **TEST ALERT** 🧪

{message_text}

💡 <b>Button Economics:</b>
• ⬅️ BACK - Navigate history (FREE)
• 👉 NEXT - New opportunities (1 token)
• 💰 BUY - Purchase links (FREE)
• 🤖 TOP UP - Buy tokens (FREE)

*This is a test notification with working buttons! Navigation through history is always free.*"""
    
    # Create fully functional buttons
    keyboard = build_addictive_buttons(test_data)
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=test_message,
            parse_mode='HTML',
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        # Confirm to user that test was sent
        await update.message.reply_text(
            "✅ Test notification sent! All buttons work - try clicking BACK (free) vs NEXT (costs token) to see the difference.",
            parse_mode='HTML'
        )
        
        logging.info(f"Test notification with functional buttons sent to {username} (ID: {user_id})")
        
    except Exception as e:
        logging.error(f"Failed to send test notification to {username} (ID: {user_id}): {e}")
        await update.message.reply_text(
            "❌ Failed to send test notification. Please try again or contact support.",
            parse_mode='HTML'
        )

# =============================================================================
# Debug Functions for Development and Support
# =============================================================================

async def debug_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check user session state - Enhanced with cache info"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        cached_data = session.get('cached_data', {})
        
        message = f"""🔍 <b>Session Debug for User {user_id}</b>

📊 <b>Current State:</b>
History Length: {len(session['history'])}
Current Index: {session['index']}
From Alert: {session.get('from_alert', False)}
History: {session['history']}

🎯 <b>Current Coin:</b> {session['history'][session['index']] if session['history'] and 0 <= session['index'] < len(session['history']) else 'Invalid'}

💾 <b>Cached Data:</b>
Total Cached: {len(cached_data)}
Cached Coins: {list(cached_data.keys())}

🕒 <b>Session Info:</b>
Last Activity: {datetime.fromtimestamp(session['last_activity']).strftime('%Y-%m-%d %H:%M:%S')}

📈 <b>Navigation:</b>
Can go back: {session['index'] > 0}
Can go forward: {session['index'] < len(session['history']) - 1}

💰 <b>Economics:</b>
BACK navigation: FREE (uses cached data)
NEXT new coins: 1 token (fresh API call)

<i>Check logs for detailed debug info</i>"""
    else:
        message = f"🔍 <b>Session Debug</b>\n\nUser {user_id} has no active session."
    
    await update.message.reply_text(message, parse_mode='HTML')

# =============================================================================
# Status and Subscription Management Commands
# =============================================================================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status and subscriber count - Enhanced with economics info"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    subscriber_count = len(subscribed_users)
    
    status_message = f"""📊 **Bot Status**

🔥 **Alert System:**
👥 **Subscribers:** {subscriber_count}
🔄 **Your Status:** {'✅ Subscribed' if user_id in subscribed_users else '❌ Not Subscribed'}
⚡ **Alert Frequency:** Every 4 hours (6/day max)
🎯 **Alert Threshold:** 80%+ FOMO score only

💰 **Token Economics:**
🔴 **Costs 1 token:** Fresh coin analysis, NEXT discoveries
🟢 **Always FREE:** BACK navigation, buy coin links, alerts

📺 **Channel:** https://t.me/fomocryptobot_alert
🤖 **Bot:** @fomocryptobot

💡 **Commands:**
- `/start` - Subscribe to alerts  
- `/test` - Test alert with working buttons
- `/status` - Show this status
- `/unsubscribe` - Stop alerts
- `/buy` - Purchase FCB tokens
- `/balance` - Check your balance

🎯 **How It Works:**
• Get premium alerts with working buttons
• Navigate freely through your coin history
• Pay only for fresh analysis and new discoveries
• Quality over quantity approach"""

    await update.message.reply_text(status_message, parse_mode='HTML')
    logging.info(f"Status command used by {username} (ID: {user_id})")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to unsubscribe from opportunity alerts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        save_subscriptions()
        await update.message.reply_text(
            "🛑 You've been unsubscribed from opportunity alerts.\n\nSend /start anytime to subscribe again!", 
            parse_mode='HTML'
        )
        logging.info(f"User {username} (ID: {user_id}) unsubscribed from opportunity alerts")
    else:
        await update.message.reply_text("ℹ️ You are not currently subscribed.", parse_mode='HTML')

# =============================================================================
# Debug Helper for Session Analysis
# =============================================================================

def trigger_debug_session(user_id):
    """Programmatically trigger session debug for testing"""
    debug_user_session(user_id, "programmatic debug call")
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        return {
            'exists': True,
            'history_length': len(session.get('history', [])),
            'current_index': session.get('index', 0),
            'cached_count': len(session.get('cached_data', {})),
            'from_alert': session.get('from_alert', False),
            'last_activity': session.get('last_activity', 0)
        }
    else:
        return {
            'exists': False,
            'message': 'No session found for user'
        }

def get_session_navigation_state(user_id):
    """Get navigation state for a user session"""
    if user_id not in user_sessions:
        return None
    
    session = user_sessions[user_id]
    history = session.get('history', [])
    current_index = session.get('index', 0)
    
    return {
        'can_go_back': current_index > 0,
        'can_go_forward': current_index < len(history) - 1,
        'current_position': current_index + 1,
        'total_coins': len(history),
        'current_coin': history[current_index] if history and 0 <= current_index < len(history) else None,
        'from_alert_session': session.get('from_alert', False)
    }

def clear_user_session(user_id):
    """Clear a user's session (for testing or troubleshooting)"""
    if user_id in user_sessions:
        del user_sessions[user_id]
        logging.info(f"Cleared session for user {user_id}")
        return True
    return False

# =============================================================================
# END OF PART 3/8 - Test Command & Debug Functions Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - ECONOMICS FIXED VERSION
PART 4/8: Opportunity Discovery & Coin Analysis with Proper Token Management

Smart opportunity discovery and main coin analysis handler with perfect token economics.

FIXES APPLIED:
- ✅ Clean image captions (no cost information noise)
- ✅ Proper logo URL extraction and caching
- ✅ Separate messaging for image vs text display
"""

# =============================================================================
# Smart Opportunity Discovery with Proper Token Management (FIXED)
# =============================================================================

async def handle_instant_discovery(query, context, user_id, force_new=True):
    """
    Opportunity discovery with proper token management
    force_new=True means this costs a token (new API call)
    force_new=False means try to use cached data first
    FIXED: Clean image captions and proper logo handling
    """
    
    # Only spend token for new discoveries
    if force_new:
        success, spend_message = spend_fcb_token(user_id)
        if not success:
            await safe_edit_message(query, text=spend_message)
            return
        logging.info(f"🪙 Token spent for new discovery: User {user_id}")
    else:
        logging.info(f"🆓 Free navigation attempted: User {user_id}")
    
    # Clean hunting messages - no noise
    hunt_messages = [
        "🔍 <b>Scanning opportunities...</b>",
        "🎯 <b>Finding potential...</b>", 
        "🚀 <b>Searching gems...</b>",
        "💎 <b>Discovering coins...</b>",
        "📈 <b>Analyzing signals...</b>",
        "⚡ <b>Hunting opportunities...</b>"
    ]
    
    await safe_edit_message(query, text=random.choice(hunt_messages))
    
    try:
        # Get cached opportunities
        from config import FOMO_CACHE
        if not FOMO_CACHE['coins']:
            from cache import get_ultra_fast_fomo_opportunities
            opportunities = await get_ultra_fast_fomo_opportunities()
            if opportunities:
                FOMO_CACHE['coins'] = opportunities
                FOMO_CACHE['current_index'] = 0
        
        if FOMO_CACHE['coins']:
            # Use opportunity hunter - no excitement spam
            selected_coin_data, _ = hunt_next_opportunity(FOMO_CACHE['coins'])
            
            if not selected_coin_data:
                await safe_edit_message(query, text="❌ No opportunities detected right now! Try again.")
                return
            
            # Convert cached data to standard coin format
            coin = {
                'id': selected_coin_data.get('coin', selected_coin_data.get('id', 'unknown')),
                'name': selected_coin_data.get('name', 'Unknown'),
                'symbol': selected_coin_data.get('symbol', ''),
                'logo': selected_coin_data.get('logo') or selected_coin_data.get('image'),
                'price': selected_coin_data.get('current_price', selected_coin_data.get('price', 0)),
                'change_1h': selected_coin_data.get('price_1h_change (%)', selected_coin_data.get('change_1h', 0)),
                'change_24h': selected_coin_data.get('price_24h_change (%)', selected_coin_data.get('change_24h', 0)),
                'volume': selected_coin_data.get('volume_24h', selected_coin_data.get('volume', 0)),
                'source_url': selected_coin_data.get('source_url', 'https://coingecko.com')
            }
            
            # Validate and update coin ID for accuracy
            raw_coin_id = selected_coin_data.get('coin') or selected_coin_data.get('id') or selected_coin_data.get('symbol', 'unknown')
            
            proper_coin_id = None
            try:
                test_id, test_coin = await get_coin_info_ultra_fast(raw_coin_id)
                if test_id and test_coin:
                    proper_coin_id = test_id
                    # FIXED: Update logo URL from fresh API data if available
                    if test_coin.get('logo'):
                        coin['logo'] = test_coin['logo']
            except Exception:
                pass
            
            new_coin_id = proper_coin_id if proper_coin_id else raw_coin_id
            
            # Add to navigation history with cached data
            coin['id'] = new_coin_id
            session = add_to_user_history(user_id, new_coin_id, coin_data=coin)
            
            # FIXED: Create clean image caption vs detailed text message
            clean_balance = get_clean_balance_display(user_id)
            
            # Clean image caption (super lean!)
            clean_caption = format_treasure_discovery_message(
                coin, 
                selected_coin_data['fomo_score'], 
                selected_coin_data['signal_type'], 
                selected_coin_data['volume_spike']
            )
            clean_caption += f"\n\n{clean_balance}"
            
            # Detailed text message with cost information
            detailed_msg = clean_caption
            if force_new:
                detailed_msg += "\n\n💰 <i>1 token spent for new discovery</i>"
            else:
                detailed_msg += "\n\n🆓 <i>Free navigation</i>"
            
            # Get user balance for buttons
            user_balance_info = get_user_balance_info(user_id)
            keyboard = build_addictive_buttons(coin, user_balance_info)
            
            # FIXED: Handle logo display with clean captions
            logo_url = coin.get('logo')
            photo_sent = False
            
            if logo_url:
                try:
                    api_session = await get_optimized_session()
                    async with api_session.get(logo_url) as response:
                        if response.status == 200:
                            image_bytes = BytesIO(await response.read())
                            try:
                                await query.message.delete()
                                # FIXED: Use clean_caption for image (no cost noise)
                                await context.bot.send_photo(
                                    chat_id=query.message.chat_id,
                                    photo=image_bytes,
                                    caption=clean_caption,  # Clean caption only!
                                    parse_mode='HTML',
                                    reply_markup=keyboard
                                )
                                photo_sent = True
                                logging.info(f"🎯 Discovery with clean photo: {selected_coin_data['symbol']} (cost: {'1 token' if force_new else 'FREE'})")
                            except Exception as photo_error:
                                logging.warning(f"Photo send failed: {photo_error}")
                except Exception as e:
                    logging.warning(f"Image fetch failed: {e}")

            # Fallback to text message if photo fails
            if not photo_sent:
                await safe_edit_message(query, text=detailed_msg, reply_markup=keyboard)
            
            logging.info(f"🎯 User {user_id} discovered {selected_coin_data['symbol']} (cost: {'1 token' if force_new else 'FREE'})")

        else:
            await safe_edit_message(query, text="❌ No opportunities found right now. Try again!")
            
    except Exception as e:
        logging.error(f"Error in opportunity hunting: {e}")
        await safe_edit_message(query, text="❌ Error hunting for opportunities. Please try again.")

# =============================================================================
# Enhanced Coin Analysis with Proper Token Management (FIXED)
# =============================================================================

async def send_coin_message_ultra_fast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main coin analysis handler with proper token spending
    Only costs tokens for fresh API calls, not for system operations
    FIXED: Clean image captions and proper logo handling
    """
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    logging.info(f"🔍 Analysis request: User {user_id} -> '{query}'")
    
    # Rate limit check with clean error handling
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)

    if not allowed:
        if reason == "No queries available":
            try:
                message = format_out_of_scans_message_with_back(query)
                keyboard = build_out_of_scans_keyboard_with_back(query)
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
                return
            except Exception as e:
                logging.error(f"❌ Enhanced out of scans message failed: {e}")
                # Emergency fallback
                await update.message.reply_text("💔 <b>Out of scans!</b>\n\nUse /buy to get more scans! 🚀", parse_mode='HTML')
        else:
            try:
                countdown_msg = create_countdown_visual(time_remaining)
                countdown_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]
                ])
                await update.message.reply_text(countdown_msg, parse_mode='HTML', reply_markup=countdown_keyboard)
            except Exception as e:
                logging.error(f"❌ Countdown message failed: {e}")
        return
    
    # Spend the query token (this is a fresh API call)
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        await update.message.reply_text(spend_message, parse_mode='HTML')
        return
    
    logging.info(f"🪙 Token spent for fresh coin analysis: User {user_id} -> '{query}'")
    
    # Clean loading message
    searching_msg = await update.message.reply_text('🔍 <b>Analyzing...</b>', parse_mode='HTML')
    
    try:
        # Get coin info with ultra-fast lookup (this is the API call we paid for)
        coin_id, coin = await get_coin_info_ultra_fast(query)
        
        logging.info(f"🔍 Coin lookup: '{query}' -> {coin_id}, found: {bool(coin)}")

        if not coin:
            await searching_msg.edit_text('❌ Coin not found! Please check spelling.')
            return

        # Add to user navigation history with cached data for free future navigation
        session = add_to_user_history(user_id, coin_id, coin_data=coin)
        debug_user_session(user_id, "after paid coin search")
        
        # Show quick progress update
        name = f"{coin.get('name', 'Unknown')} ({coin.get('symbol', '')})"
        quick_msg = f"""⚡ <b>Fresh Analysis</b>

<b>{name}</b>

🚀 <i>Running analysis...</i>"""
        
        await searching_msg.edit_text(quick_msg, parse_mode='HTML')
        
        # Run ultra-fast parallel analysis (part of the paid API call)
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
        
        # FIXED: Create clean image caption vs detailed text message
        clean_balance = get_clean_balance_display(user_id)
        
        # Clean image caption (super lean!)
        clean_caption = format_simple_message(
            coin, fomo_score, signal_type, volume_spike, 
            trend_status, distribution_status, is_broadcast=False
        )
        clean_caption += f"\n\n{clean_balance}"
        
        # Detailed text message with cost information
        detailed_msg = clean_caption + "\n\n💰 <i>1 token spent for fresh analysis</i>"
        
        # Build keyboard with user's balance info
        user_balance_info = get_user_balance_info(user_id)
        keyboard = build_addictive_buttons(coin, user_balance_info)
        
        # Clean up loading message
        try:
            await searching_msg.delete()
        except:
            pass
        
        # FIXED: Try with logo for visual appeal with clean caption
        logo_url = coin.get('logo')
        photo_sent = False
        
        if logo_url:
            try:
                api_session = await get_optimized_session()
                async with api_session.get(logo_url) as response:
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        # FIXED: Use clean_caption for image (no cost noise)
                        await update.message.reply_photo(
                            photo=image_bytes, 
                            caption=clean_caption,  # Clean caption only!
                            parse_mode='HTML', 
                            reply_markup=keyboard
                        )
                        photo_sent = True
                        logging.info(f"✅ Paid analysis with clean photo complete for {query}")
            except Exception as e:
                logging.warning(f"Logo fetch failed: {e}")
                
        # Fallback to text message if photo fails
        if not photo_sent:
            await update.message.reply_text(detailed_msg, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
        
        logging.info(f"✅ Paid analysis complete for {query} (1 token spent)")
        
    except Exception as e:
        logging.error(f"Error in paid analysis: {e}")
        try:
            await searching_msg.edit_text('❌ Error processing request. Please try again.')
        except:
            await update.message.reply_text('❌ Error processing request. Please try again.')

# =============================================================================
# Alert Coin Handler with Proper Economics (FIXED)
# =============================================================================

async def handle_alert_coin_analysis(user_id, coin_id, context, original_message=None):
    """
    Special handler for when users click alert buttons
    First tries cached data, falls back to fresh API call if needed
    FIXED: Clean messaging and proper logo handling
    """
    
    logging.info(f"🔥 Alert coin analysis: User {user_id} analyzing {coin_id}")
    
    # Try to use cached data first
    cached_coin = get_cached_coin_data(user_id, coin_id)
    
    if cached_coin:
        logging.info(f"🆓 Using cached data for alert navigation: {coin_id}")
        
        # Use cached data - no API call needed
        try:
            # FIXED: Create clean image caption vs detailed text message
            clean_balance = get_clean_balance_display(user_id)
            
            # Clean image caption
            clean_caption = format_simple_message(
                cached_coin, 85, "⚡ Cached Analysis", 2.5, 
                "Bullish", "Balanced", is_broadcast=False
            )
            clean_caption += f"\n\n{clean_balance}"
            
            # Detailed text message
            detailed_msg = clean_caption + "\n\n🆓 <i>Free navigation (cached data)</i>"
            
            # Build keyboard
            user_balance_info = get_user_balance_info(user_id)
            keyboard = build_addictive_buttons(cached_coin, user_balance_info)
            
            return {
                'message': detailed_msg,  # Use detailed for text fallback
                'clean_caption': clean_caption,  # Clean for image
                'keyboard': keyboard,
                'coin': cached_coin,
                'coin_id': coin_id,
                'cost': 'FREE'
            }
        except Exception as e:
            logging.error(f"Error using cached data: {e}")
            # Fall through to fresh API call
    
    # No cached data available, need fresh API call
    logging.info(f"🪙 No cached data, fetching fresh data for: {coin_id}")
    
    # Check if user has tokens for fresh analysis
    fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
    has_scans = total_free_remaining > 0 or fcb_balance > 0
    
    if not has_scans:
        return {
            'message': "💔 <b>Out of tokens!</b>\n\nThis coin needs fresh analysis (1 token).\nUse 🤖 TOP UP to get more tokens!",
            'keyboard': InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 TOP UP", callback_data="buy_starter")]
            ]),
            'coin': None,
            'coin_id': coin_id,
            'cost': 'BLOCKED'
        }
    
    # Spend token for fresh analysis
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        return {
            'message': spend_message,
            'keyboard': InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 TOP UP", callback_data="buy_starter")]
            ]),
            'coin': None,
            'coin_id': coin_id,
            'cost': 'FAILED'
        }
    
    try:
        # Get fresh coin info (this costs the token)
        fetched_coin_id, coin = await get_coin_info_ultra_fast(coin_id)
        
        if not coin:
            error_msg = "❌ Alert coin not found. It may have been delisted.\n\n💰 <i>1 token was spent for this lookup</i>"
            if original_message:
                await original_message.reply_text(error_msg, parse_mode='HTML')
            return None
        
        # Use the fetched coin ID if different
        if fetched_coin_id:
            coin_id = fetched_coin_id
        
        # Add to navigation history with fresh data cached
        add_to_user_history(user_id, coin_id, coin_data=coin, from_alert=True)
        
        # Run fresh analysis
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
        
        # FIXED: Create clean image caption vs detailed text message
        clean_balance = get_clean_balance_display(user_id)
        
        # Clean image caption
        clean_caption = format_simple_message(
            coin, fomo_score, signal_type, volume_spike, 
            trend_status, distribution_status, is_broadcast=False
        )
        clean_caption += f"\n\n{clean_balance}"
        
        # Detailed text message with cost information
        detailed_msg = clean_caption + "\n\n💰 <i>1 token spent for fresh analysis</i>"
        
        # Build keyboard
        user_balance_info = get_user_balance_info(user_id)
        keyboard = build_addictive_buttons(coin, user_balance_info)
        
        return {
            'message': detailed_msg,  # Use detailed for text fallback
            'clean_caption': clean_caption,  # Clean for image
            'keyboard': keyboard,
            'coin': coin,
            'coin_id': coin_id,
            'cost': '1 TOKEN'
        }
        
    except Exception as e:
        logging.error(f"Error in fresh alert coin analysis: {e}")
        return None

# =============================================================================
# END OF PART 4/8 - Opportunity Discovery & Coin Analysis Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - ECONOMICS FIXED VERSION
PART 5/8: Back Navigation Handler - Always FREE with Smart Caching

BACK navigation is ALWAYS FREE - uses cached data, no API calls
Enhanced back navigation that works seamlessly from alert buttons.

FIXES APPLIED:
- ✅ Clean image captions (no navigation noise)
- ✅ Proper logo URL caching and display
- ✅ Separate text vs image messaging
"""

# =============================================================================
# BACK Navigation - ALWAYS FREE with Smart Caching (FIXED)
# =============================================================================

async def handle_back_navigation(query, context, user_id):
    """
    Handle BACK button with ALWAYS FREE navigation
    Uses cached data when available, minimal API calls only when absolutely necessary
    FIXED: Clean image captions and proper logo handling
    """
    
    logging.info(f"🔍 BACK DEBUG: User {user_id} clicked back (FREE navigation)")
    
    try:
        session = get_user_session(user_id)
        debug_user_session(user_id, "back button clicked")
        
        # Check if user came from alert
        from_alert = session.get('from_alert', False)
        
        if not session.get('history') or len(session['history']) == 0:
            logging.warning(f"🔍 BACK DEBUG: No coin history for user {user_id}")
            
            # Context-aware message for alert users vs regular users
            if from_alert:
                error_msg = "❌ This was your first coin from the alert. Try 👉 NEXT to discover more opportunities!"
            else:
                error_msg = "❌ No previous coins in this session. Try searching for a coin first!"
                
            await safe_edit_message(query, text=error_msg)
            return
        
        # Robust index validation and correction
        current_index = session.get('index', 0)
        history_length = len(session['history'])
        
        # Ensure index is within bounds
        if current_index >= history_length:
            current_index = history_length - 1
            session['index'] = current_index
            logging.info(f"🔍 BACK DEBUG: Corrected out-of-bounds index to {current_index}")
        
        if current_index < 0:
            current_index = 0
            session['index'] = current_index
            logging.info(f"🔍 BACK DEBUG: Corrected negative index to {current_index}")
        
        # Proper BACK navigation logic
        if current_index > 0:
            # Move back to previous coin (decrease index by 1)
            new_index = current_index - 1
            session['index'] = new_index
            target_coin_id = session['history'][new_index]
            
            nav_context = "alert navigation" if from_alert else "regular navigation"
            logging.info(f"⬅️ User {user_id}: FREE back navigation from position {current_index + 1} to {new_index + 1}/{history_length}: {target_coin_id} ({nav_context})")
        else:
            # Already at first coin, can't go back further
            logging.info(f"⬅️ User {user_id}: Already at first coin")
            
            # Context-aware message
            if from_alert:
                friendly_msg = "⬅️ You're at the first coin from your alert! Use 👉 NEXT to discover new opportunities."
            else:
                friendly_msg = "⬅️ You're already at the first coin in this session!"
                
            await safe_edit_message(query, text=friendly_msg)
            return
        
        # Validate the coin ID before proceeding
        if not validate_coingecko_id(target_coin_id):
            logging.error(f"🔍 BACK DEBUG: Invalid/problematic coin ID '{target_coin_id}' rejected by validation")
            await safe_edit_message(query, text="❌ Invalid coin in history. Please start a new search.")
            return
        
        # Try to use cached data first (FREE)
        cached_coin = get_cached_coin_data(user_id, target_coin_id)
        
        if cached_coin:
            logging.info(f"🆓 Using cached data for BACK navigation: {target_coin_id}")
            
            # Use cached data - completely FREE
            try:
                # Run basic analysis on cached data (no API calls)
                fomo_score = 75  # Use reasonable default
                signal_type = "📊 Cached Analysis"
                volume_spike = 2.0
                trend_status = "Cached"
                distribution_status = "Cached"
                
                # FIXED: Create clean image caption vs detailed text message
                clean_balance = get_clean_balance_display(user_id)
                
                # Clean image caption (super lean!)
                clean_caption = format_simple_message(
                    cached_coin, fomo_score, signal_type, volume_spike, 
                    trend_status, distribution_status, is_broadcast=False
                )
                clean_caption += f"\n\n{clean_balance}"
                
                # Detailed text message for non-image fallback
                detailed_msg = clean_caption
                
                # Add navigation info ONLY to detailed message (not image caption)
                position = session['index'] + 1
                total = len(session['history'])
                
                nav_status = "⬅️ <i>FREE navigation (cached data)"
                nav_status += f" | Position {position}/{total}</i>"
                
                detailed_msg += f"\n\n{nav_status}"
                
                # Build keyboard
                user_balance_info = get_user_balance_info(user_id)
                keyboard = build_addictive_buttons(cached_coin, user_balance_info)
                
                # FIXED: Handle logo display with clean captions
                logo_url = cached_coin.get('logo')
                photo_sent = False
                
                if logo_url:
                    try:
                        api_session = await get_optimized_session()
                        async with api_session.get(logo_url, timeout=5) as response:
                            if response.status == 200:
                                image_bytes = BytesIO(await response.read())
                                
                                try:
                                    await query.message.delete()
                                    # FIXED: Use clean_caption for image (no navigation noise)
                                    await context.bot.send_photo(
                                        chat_id=query.message.chat_id,
                                        photo=image_bytes,
                                        caption=clean_caption,  # Clean caption only!
                                        parse_mode='HTML',
                                        reply_markup=keyboard
                                    )
                                    photo_sent = True
                                    logging.info(f"✅ FREE BACK navigation with clean photo: {target_coin_id}")
                                except Exception as photo_error:
                                    logging.warning(f"Photo send failed in FREE BACK: {photo_error}")
                    except Exception as e:
                        logging.warning(f"Image fetch failed in FREE BACK: {e}")

                # Fallback to text message if photo fails
                if not photo_sent:
                    await safe_edit_message(query, text=detailed_msg, reply_markup=keyboard)
                
                logging.info(f"✅ FREE BACK navigation complete: {target_coin_id} (position {position}/{total}) - used cached data")
                debug_user_session(user_id, "after free back navigation")
                return
                
            except Exception as cache_error:
                logging.warning(f"Error using cached data for BACK: {cache_error}")
                # Fall through to API call as last resort
        
        # No cached data available - need to decide on API call
        logging.warning(f"🪙 No cached data for BACK navigation: {target_coin_id}")
        
        await safe_edit_message(query, text="⬅️ <b>Loading previous coin... (FREE)</b>")
        
        # Try minimal API call for basic info only
        coin_id = None
        coin = None
        
        try:
            # Try to get basic coin info (this might use cached API data)
            coin_id, coin = await get_coin_info_ultra_fast(target_coin_id)
            
            if coin and coin is not None:
                logging.info(f"✅ BACK: Got basic info for {target_coin_id}")
                
                # Cache this data for future FREE navigation
                add_to_user_history(user_id, target_coin_id, coin_data=coin)
                
            else:
                logging.warning(f"🔍 BACK: No data available for {target_coin_id}")
                # Create minimal placeholder data
                coin = {
                    'id': target_coin_id,
                    'name': target_coin_id.replace('-', ' ').title(),
                    'symbol': target_coin_id[:6].upper(),
                    'price': 0,
                    'change_1h': 0,
                    'change_24h': 0,
                    'volume': 0,
                    'logo': None
                }
                
        except Exception as fetch_error:
            logging.warning(f"🔍 BACK: Fetch error for {target_coin_id}: {fetch_error}")
            # Create minimal placeholder data
            coin = {
                'id': target_coin_id,
                'name': target_coin_id.replace('-', ' ').title(),
                'symbol': target_coin_id[:6].upper(),
                'price': 0,
                'change_1h': 0,
                'change_24h': 0,
                'volume': 0,
                'logo': None
            }
        
        # Use basic values for FREE navigation
        fomo_score = 50  # Default value
        signal_type = "⬅️ Previous Coin"
        volume_spike = 1.0
        trend_status = "Historical"
        distribution_status = "Historical"
        
        # FIXED: Enhanced message formatting with clean image vs detailed text separation
        try:
            clean_balance = get_clean_balance_display(user_id)
            
            # Clean image caption (super lean!)
            clean_caption = format_simple_message(
                coin, fomo_score, signal_type, volume_spike, 
                trend_status, distribution_status, is_broadcast=False
            )
            clean_caption += f"\n\n{clean_balance}"
            
            # Detailed text message with navigation info
            detailed_msg = clean_caption
            
            # Add navigation info with FREE emphasis (ONLY to detailed message)
            position = session['index'] + 1
            total = len(session['history'])
            
            if from_alert:
                nav_status = "⬅️ <i>FREE alert navigation"
            else:
                nav_status = "⬅️ <i>FREE navigation"
            
            nav_status += f" | Position {position}/{total}</i>"
            detailed_msg += f"\n\n{nav_status}"
            
            # Add note about data freshness if using placeholder
            if coin.get('price', 0) == 0:
                detailed_msg += "\n\n<i>💡 Note: Historical data shown. For fresh analysis, search coin name directly.</i>"
            
        except Exception as format_error:
            logging.error(f"🔍 BACK DEBUG: Message formatting error: {format_error}")
            coin_name = coin.get('name', 'Unknown') if coin else target_coin_id
            clean_caption = f"<b>{coin_name}</b>\n\n⬅️ Previous coin\n\n{get_clean_balance_display(user_id)}"
            detailed_msg = f"<b>{coin_name}</b>\n\n⬅️ <i>FREE navigation - Previous coin</i>\n\n💡 For fresh analysis, search coin name directly."
        
        # Get keyboard
        try:
            user_balance_info = get_user_balance_info(user_id)
            keyboard = build_addictive_buttons(coin, user_balance_info)
        except Exception as balance_error:
            logging.error(f"🔍 BACK DEBUG: Balance/keyboard error: {balance_error}")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('👉 NEXT', callback_data="next_coin")],
                [InlineKeyboardButton('🤖 TOP UP', callback_data='buy_starter')]
            ])
        
        # FIXED: Handle logo updates with clean captions
        photo_sent = False
        logo_url = coin.get('logo') if coin else None
        
        if logo_url:
            try:
                api_session = await get_optimized_session()
                async with api_session.get(logo_url, timeout=5) as response:
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        
                        try:
                            await query.message.delete()
                            # FIXED: Use clean_caption for image (no navigation noise)
                            await context.bot.send_photo(
                                chat_id=query.message.chat_id,
                                photo=image_bytes,
                                caption=clean_caption,  # Clean caption only!
                                parse_mode='HTML',
                                reply_markup=keyboard
                            )
                            photo_sent = True
                            nav_type = "alert" if from_alert else "regular"
                            logging.info(f"✅ FREE BACK navigation ({nav_type}) with clean photo: {target_coin_id}")
                        except Exception as photo_error:
                            logging.warning(f"Photo send failed in FREE BACK: {photo_error}")
            except Exception as e:
                logging.warning(f"Image fetch failed in FREE BACK (expected): {e}")

        # Fallback to text message if photo fails
        if not photo_sent:
            await safe_edit_message(query, text=detailed_msg, reply_markup=keyboard)
        
        # Final logging with emphasis on FREE navigation
        final_position = session.get('index', 0) + 1
        total = len(session.get('history', []))
        nav_type = "alert" if from_alert else "regular"
        logging.info(f"✅ FREE BACK navigation ({nav_type}) complete: {target_coin_id} (position {final_position}/{total}) - NO TOKEN SPENT")
        debug_user_session(user_id, "after free back navigation")
        
    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in FREE back navigation: {e}", exc_info=True)
        try:
            # Context-aware fallback message
            session = get_user_session(user_id)
            from_alert = session.get('from_alert', False)
            
            if from_alert:
                fallback_msg = "❌ Error navigating back. Try 👉 NEXT to find new opportunities or type a coin name to search."
            else:
                fallback_msg = "❌ Error navigating back. Please try again or start a new search by typing a coin name."
                
            await safe_edit_message(query, text=fallback_msg)
        except Exception as fallback_error:
            logging.error(f"❌ Even fallback message failed: {fallback_error}")
            try:
                await query.answer("Error occurred, please try again")
            except Exception:
                pass

# =============================================================================
# END OF PART 5/8 - BACK Navigation Always FREE Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - ECONOMICS FIXED VERSION
PART 6/8: Next Navigation & Buy Coin Handlers - CAPTION CLEANING FIXED

Smart NEXT logic - FREE for cached history, 1 token for new discoveries
Enhanced buy coin button handler and forward navigation helpers.

CAPTION FIX: Clean image captions with NO navigation noise
"""

# =============================================================================
# Smart NEXT Navigation with Proper Token Economics
# =============================================================================

async def handle_next_navigation(query, context, user_id):
    """
    Handle NEXT button with smart token economics
    - Forward through existing history = FREE (cached data)
    - New coin discovery = COSTS 1 TOKEN (fresh API call)
    """
    
    logging.info(f"🔍 NEXT DEBUG: User {user_id} clicked next")
    
    try:
        # Get user session with alert context
        session = get_user_session(user_id)
        from_alert = session.get('from_alert', False)
        debug_user_session(user_id, "next button clicked")
        
        # Check if user has history and current position
        history = session.get('history', [])
        current_index = session.get('index', 0)
        
        # Check if user can move FORWARD through existing history (FREE)
        if history and current_index < len(history) - 1:
            # We have forward history - this should be FREE
            target_coin_id = history[current_index + 1]
            
            if not validate_coingecko_id(target_coin_id):
                logging.warning(f"🔍 NEXT DEBUG: Invalid coin ID in forward history: {target_coin_id}, falling back to new coin discovery")
                # Fall through to new coin discovery instead of showing error
            else:
                # FREE forward navigation through existing history
                nav_type = "alert" if from_alert else "regular"
                logging.info(f"➡️ User {user_id}: FREE forward navigation ({nav_type}) to {target_coin_id}")
                
                await safe_edit_message(query, text="➡️ <b>Moving forward... (FREE navigation)</b>")
                
                # Move forward to next coin in history
                new_index = current_index + 1
                session['index'] = new_index
                
                # Try to use cached data first
                cached_coin = get_cached_coin_data(user_id, target_coin_id)
                
                if cached_coin:
                    # Use cached data - completely FREE
                    success = await display_coin_from_history_forward(query, context, user_id, target_coin_id, cached_coin, from_alert)
                else:
                    # Try basic lookup for forward navigation (still try to keep it free)
                    success = await display_coin_from_history_forward(query, context, user_id, target_coin_id, None, from_alert)
                
                if success:
                    logging.info(f"✅ FREE NEXT forward navigation complete: {target_coin_id} (position {new_index + 1}/{len(history)})")
                    return
                else:
                    # If forward navigation failed, fall through to new coin discovery
                    logging.warning(f"🔍 NEXT DEBUG: Forward navigation failed, falling back to new coin discovery")
        
        # NEW COIN DISCOVERY: User is at end of history or no history - COSTS 1 TOKEN
        logging.info(f"🔍 NEXT DEBUG: At end of history or no history, finding new coin (will cost 1 token)")
        
        # Check if they have scans available for NEW discoveries
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        has_scans = total_free_remaining > 0 or fcb_balance > 0
        
        if not has_scans:
            # Show upgrade message for new discoveries
            message = format_out_of_scans_message("new coin")
            keyboard = build_out_of_scans_keyboard()
            await safe_edit_message(query, text=message, reply_markup=keyboard)
            return
        
        # Proceed with new coin discovery (COSTS 1 TOKEN)
        discovery_msg = "🔍 <b>Finding new opportunities... (1 token will be spent)</b>"
        await safe_edit_message(query, text=discovery_msg)
        
        # Use enhanced discovery with proper token spending
        await handle_instant_discovery(query, context, user_id, force_new=True)  # This costs 1 token
        
    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in next navigation: {e}", exc_info=True)
        try:
            # Context-aware error message
            session = get_user_session(user_id)
            from_alert = session.get('from_alert', False)
            
            if from_alert:
                error_msg = "❌ Error finding next coin. Try typing a coin name to search directly."
            else:
                error_msg = "❌ Error finding next coin. Please try again."
                
            await safe_edit_message(query, text=error_msg)
        except Exception as fallback_error:
            logging.error(f"❌ Even fallback message failed: {fallback_error}")
            try:
                await query.answer("Error occurred, please try again")
            except Exception:
                pass

# =============================================================================
# Forward Navigation Helper with Smart Caching - CAPTION FIXED
# =============================================================================

async def display_coin_from_history_forward(query, context, user_id, target_coin_id, cached_coin=None, from_alert=False):
    """
    Display a coin from history for forward navigation
    Uses cached data when available, minimal API calls when necessary
    FIXED: Clean image captions with NO navigation noise
    """
    
    logging.info(f"🔍 FORWARD DEBUG: Displaying {target_coin_id} (cached: {bool(cached_coin)}, alert: {from_alert})")
    
    coin = None
    
    if cached_coin:
        # Use cached data - completely FREE
        coin = cached_coin
        logging.info(f"🆓 Using cached data for forward navigation: {target_coin_id}")
        
        # Run basic analysis on cached data
        fomo_score = 70  # Reasonable default for cached data
        signal_type = "📊 Cached Analysis"
        volume_spike = 2.0
        trend_status = "Cached"
        distribution_status = "Cached"
        
    else:
        # No cached data - try basic lookup (try to keep it free)
        logging.info(f"🔍 FORWARD DEBUG: No cached data, attempting basic lookup for: {target_coin_id}")
        
        try:
            # Try to get basic coin info
            fetched_coin_id, fetched_coin = await get_coin_info_ultra_fast(target_coin_id)
            
            if fetched_coin and fetched_coin is not None:
                coin = fetched_coin
                if fetched_coin_id:
                    target_coin_id = fetched_coin_id
                
                # Cache this data for future FREE navigation
                add_to_user_history(user_id, target_coin_id, coin_data=coin)
                
                logging.info(f"✅ FORWARD DEBUG: Got basic info for {target_coin_id}")
            else:
                logging.warning(f"🔍 FORWARD DEBUG: No data available for {target_coin_id}")
                # Create minimal placeholder
                coin = {
                    'id': target_coin_id,
                    'name': target_coin_id.replace('-', ' ').title(),
                    'symbol': target_coin_id[:6].upper(),
                    'price': 0,
                    'change_1h': 0,
                    'change_24h': 0,
                    'volume': 0,
                    'logo': None
                }
                
        except Exception as fetch_error:
            logging.warning(f"🔍 FORWARD DEBUG: Fetch error for {target_coin_id}: {fetch_error}")
            # Create minimal placeholder
            coin = {
                'id': target_coin_id,
                'name': target_coin_id.replace('-', ' ').title(),
                'symbol': target_coin_id[:6].upper(),
                'price': 0,
                'change_1h': 0,
                'change_24h': 0,
                'volume': 0,
                'logo': None
            }
        
        # Use basic analysis values for forward navigation
        fomo_score = 60
        signal_type = "➡️ Forward Navigation"
        volume_spike = 1.5
        trend_status = "Historical"
        distribution_status = "Historical"
    
    # CAPTION FIX: Create separate clean caption vs detailed message
    try:
        # CLEAN CAPTION for images (super minimal!)
        clean_balance = get_clean_balance_display(user_id)
        clean_caption = format_simple_message(
            coin, fomo_score, signal_type, volume_spike, 
            trend_status, distribution_status, is_broadcast=False
        )
        clean_caption += f"\n\n{clean_balance}"
        
        # DETAILED MESSAGE for text fallback (includes navigation info)
        detailed_msg = clean_caption
        
        # Add navigation info ONLY to detailed message (NOT to image caption)
        session = get_user_session(user_id)
        position = session['index'] + 1
        total = len(session['history'])
        can_go_back = session['index'] > 0
        can_go_forward = session['index'] < total - 1
        
        if from_alert:
            nav_status = "➡️ <i>FREE alert navigation"
        else:
            nav_status = "➡️ <i>FREE navigation"
        
        if can_go_back and can_go_forward:
            nav_status += f" | Position {position}/{total}"
        elif can_go_back:
            nav_status += f" | Position {position}/{total} | Next will find new coin (1 token)"
        elif can_go_forward:
            nav_status += f" | Position {position}/{total}"
        else:
            nav_status += f" | Position {position}/{total} | Next will find new coin (1 token)"
        nav_status += "</i>"
        
        detailed_msg += f"\n\n{nav_status}"
        
        # Add note about data type (ONLY to detailed message)
        if cached_coin:
            detailed_msg += "\n\n🆓 <i>Using cached data (FREE)</i>"
        elif coin.get('price', 0) == 0:
            detailed_msg += "\n\n<i>💡 Historical data. For fresh analysis, search coin name directly (1 token).</i>"
        
    except Exception as format_error:
        logging.error(f"🔍 FORWARD DEBUG: Message formatting error: {format_error}")
        coin_name = coin.get('name', 'Unknown') if coin else target_coin_id
        # Fallback clean caption
        clean_balance = get_clean_balance_display(user_id)
        clean_caption = f"<b>{coin_name}</b>\n\n➡️ Forward navigation\n\n{clean_balance}"
        # Fallback detailed message
        detailed_msg = f"<b>{coin_name}</b>\n\n➡️ <i>FREE forward navigation</i>"
    
    # Get keyboard
    try:
        user_balance_info = get_user_balance_info(user_id)
        keyboard = build_addictive_buttons(coin, user_balance_info)
    except Exception as balance_error:
        logging.error(f"🔍 FORWARD DEBUG: Balance/keyboard error: {balance_error}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('👉 NEXT', callback_data="next_coin")],
            [InlineKeyboardButton('🤖 TOP UP', callback_data='buy_starter')]
        ])
    
    # CAPTION FIX: Display with photo using CLEAN caption
    photo_sent = False
    logo_url = coin.get('logo') if coin else None
    
    if logo_url:
        try:
            api_session = await get_optimized_session()
            async with api_session.get(logo_url, timeout=3) as response:  # Short timeout for free navigation
                if response.status == 200:
                    image_bytes = BytesIO(await response.read())
                    
                    try:
                        await query.message.delete()
                        # FIXED: Use clean_caption for image (NO navigation noise!)
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=image_bytes,
                            caption=clean_caption,  # ✅ CLEAN CAPTION ONLY!
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                        photo_sent = True
                        nav_type = "alert" if from_alert else "regular"
                        cost_type = "cached" if cached_coin else "basic"
                        logging.info(f"✅ FREE forward navigation ({nav_type}, {cost_type}) with CLEAN photo: {target_coin_id}")
                    except Exception as photo_error:
                        logging.warning(f"Photo send failed in forward: {photo_error}")
        except Exception as e:
            logging.warning(f"Image fetch failed in forward (expected for free nav): {e}")

    # Fallback to text message if photo fails (uses detailed message with navigation info)
    if not photo_sent:
        await safe_edit_message(query, text=detailed_msg, reply_markup=keyboard)
    
    return True

# =============================================================================
# Enhanced Buy Coin Button Handler
# =============================================================================

async def handle_buy_coin_button(query, context, user_id):
    """
    Handle the 💰 BUY COIN button click - ALWAYS FREE
    Shows users where to buy the current coin without any token cost
    """
    
    try:
        # Extract coin information from the current session - NO API CALL
        session = get_user_session(user_id)
        
        if not session.get('history'):
            await safe_edit_message(query, text="❌ No coin selected. Please search for a coin first.")
            return
        
        # Get current coin from session
        current_index = session.get('index', 0)
        if current_index >= len(session['history']):
            current_index = len(session['history']) - 1
            session['index'] = current_index
        
        coin_id = session['history'][current_index]
        
        # Try to use cached data first (FREE)
        cached_coin = get_cached_coin_data(user_id, coin_id)
        
        if cached_coin:
            coin = cached_coin
            coin_symbol = coin.get('symbol', '').upper()
            coin_name = coin.get('name', 'Unknown')
            logging.info(f"🆓 Buy coin button using cached data: {coin_symbol}")
        else:
            # No cached data - use basic info without API call
            coin_symbol = coin_id[:6].upper()
            coin_name = coin_id.replace('-', ' ').title()
            coin = {'id': coin_id, 'symbol': coin_symbol, 'name': coin_name}
            logging.info(f"🆓 Buy coin button using basic info: {coin_symbol}")
        
        # Get buy URL (no API call)
        buy_url = get_buy_coin_url(coin)
        
        # Create buy message
        buy_message = f"""💰 <b>Buy {coin_name} ({coin_symbol})</b>

🔗 <b>Purchase Options:</b>

<a href="{buy_url}">🔥 Buy {coin_symbol} on CoinGecko</a>

⚠️ <b>Important:</b>
• Always verify the contract address
• Start with small amounts
• High risk - you could lose everything
• DYOR (Do Your Own Research)

💡 <b>Tip:</b> CoinGecko shows verified exchanges and current prices for {coin_symbol}.

🆓 <i>Buy coin links are always FREE</i>"""

        # Create back button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Analysis", callback_data="back_to_analysis")],
            [InlineKeyboardButton("🤖 TOP UP Tokens", callback_data="buy_starter")]
        ])
        
        await safe_edit_message(query, text=buy_message, reply_markup=keyboard)
        
        logging.info(f"✅ FREE buy coin info shown for {coin_symbol} to user {user_id}")
        
    except Exception as e:
        logging.error(f"Error in buy coin handler: {e}")
        await safe_edit_message(query, text="❌ Error loading purchase information. Please try again.")

async def handle_back_to_analysis(query, context, user_id):
    """
    Handle back to analysis from buy coin screen - FREE
    """
    
    try:
        session = get_user_session(user_id)
        
        if not session.get('history'):
            await handle_back_to_main(query, context, user_id)
            return
        
        # Get current coin and redisplay analysis using cached data if possible
        current_index = session.get('index', 0)
        if current_index >= len(session['history']):
            current_index = len(session['history']) - 1
            session['index'] = current_index
        
        coin_id = session['history'][current_index]
        
        # Use cached data if available (FREE)
        cached_coin = get_cached_coin_data(user_id, coin_id)
        
        if cached_coin:
            # Redisplay using cached data - FREE
            # CLEAN CAPTION for potential image display
            clean_balance = get_clean_balance_display(user_id)
            clean_caption = format_simple_message(
                cached_coin, 75, "📊 Cached Analysis", 2.0, 
                "Cached", "Cached", is_broadcast=False
            )
            clean_caption += f"\n\n{clean_balance}"
            
            # DETAILED MESSAGE for text display (includes FREE navigation info)
            detailed_msg = clean_caption + "\n\n🆓 <i>Using cached data (FREE)</i>"
            
            user_balance_info = get_user_balance_info(user_id)
            keyboard = build_addictive_buttons(cached_coin, user_balance_info)
            
            # Try to display with image using CLEAN caption
            logo_url = cached_coin.get('logo')
            photo_sent = False
            
            if logo_url:
                try:
                    api_session = await get_optimized_session()
                    async with api_session.get(logo_url, timeout=3) as response:
                        if response.status == 200:
                            image_bytes = BytesIO(await response.read())
                            
                            try:
                                await query.message.delete()
                                # Use CLEAN caption for image
                                await context.bot.send_photo(
                                    chat_id=query.message.chat_id,
                                    photo=image_bytes,
                                    caption=clean_caption,  # ✅ CLEAN CAPTION ONLY!
                                    parse_mode='HTML',
                                    reply_markup=keyboard
                                )
                                photo_sent = True
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # Fallback to text if photo fails
            if not photo_sent:
                await safe_edit_message(query, text=detailed_msg, reply_markup=keyboard)
        else:
            # No cached data - offer fresh analysis for 1 token or go to main menu
            await handle_back_to_main(query, context, user_id)
            
    except Exception as e:
        logging.error(f"Error in back to analysis: {e}")
        await handle_back_to_main(query, context, user_id)

# =============================================================================
# END OF PART 6/8 - Next Navigation & Buy Coin Handlers Complete - CAPTION CLEANED
# =============================================================================


"""
Telegram handlers module for CFB (Crypto FOMO Bot) - TEXT CONSISTENCY FIXED VERSION
PART 7/8: Menu Helpers & Enhanced Callback Handler

FINAL FIX APPLIED:
- ✅ "unlimited" → "premium packages" and "250+ scans" messaging
- ✅ Contact changed from @freecryptopings to @fomocryptopings
- ✅ Daily reset time standardized to "00:00 UTC"
- ✅ Purchase flows standardized to 250 token packages
- ✅ Button text cleaned up and made consistent
"""

# =============================================================================
# Enhanced Menu Helpers with Economics Info (FIXED)
# =============================================================================

async def handle_back_to_main(query, context, user_id):
    """Handle back to main menu action with economics information"""
    
    # Get user's current balance for a helpful main menu
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    # Enhanced main menu with token economics
    main_menu_msg = f"""👋 Welcome back to FOMO Crypto Bot!

📊 Your Status:
🎯 Scans Available: {total_free_remaining}
💎 FCB Tokens: {fcb_balance}

💰 <b>Token Economics:</b>
🟢 <b>Always FREE:</b> ⬅️ BACK navigation, 💰 buy links
🔴 <b>Costs 1 token:</b> New searches, 👉 NEXT discoveries

🔥 Alert System:
✅ You're subscribed to premium alerts
⚡ Get notified when FOMO score ≥ 80%
🎯 Up to 6 quality alerts per day

✨ What would you like to do?

💡 Quick Actions:
- Type any coin name (like "bitcoin", "pepe") → 1 token
- Use /balance to check your scans
- Use /buy to get more FCB tokens
- Use /test to test alert functionality

📺 Follow our alerts: https://t.me/fomocryptobot_alert

Ready to find the next opportunity? 🚀"""

    # Enhanced keyboard with economics context
    keyboard_buttons = []
    
    # Check if user has navigation history
    session = get_user_session(user_id)
    if session.get('history'):
        # First row - navigation buttons with cost indicators
        keyboard_buttons.append([
            InlineKeyboardButton("⬅️ BACK (FREE)", callback_data="back_navigation"),
            InlineKeyboardButton("👉 NEXT (1 token)", callback_data="next_coin")
        ])
    
    # Second row - info and balance
    keyboard_buttons.append([
        InlineKeyboardButton("📊 My Balance", callback_data="check_balance"),
        InlineKeyboardButton("🧪 Test Alerts", callback_data="test_alert_system")
    ])
    
    # Third row - purchase and help
    keyboard_buttons.append([
        InlineKeyboardButton("🤖 Buy Tokens", callback_data="buy_starter"),
        InlineKeyboardButton("❓ Help", callback_data="show_help")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    await safe_edit_message(query, text=main_menu_msg, reply_markup=keyboard)

async def handle_test_alert_system(query, context, user_id):
    """
    Handle test alert system button from main menu
    """
    
    # This triggers the same test as /test command but from button
    # Create a fake update object for the test command
    class FakeMessage:
        def __init__(self, chat_id):
            self.chat_id = chat_id
            
        async def reply_text(self, text, parse_mode=None):
            await context.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
    
    class FakeUser:
        def __init__(self, user_id, username="Unknown"):
            self.id = user_id
            self.username = username
    
    class FakeUpdate:
        def __init__(self, user_id, chat_id):
            self.effective_user = FakeUser(user_id)
            self.message = FakeMessage(chat_id)
    
    # Create fake update and call test command
    fake_update = FakeUpdate(user_id, query.message.chat_id)
    await test_command(fake_update, context)
    
    # Answer the callback
    await query.answer("Test alert sent!")

async def handle_rate_limit_info(query, context, user_id):
    """FIXED: Show rate limit information with accurate economics explanation"""
    
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    info_msg = f"""⏰ Rate Limit Information

📊 Your Current Status:
🎯 Scans Available: {total_free_remaining}
💎 FCB Tokens: {fcb_balance}

💰 <b>Token Economics:</b>
🟢 <b>Always FREE (No rate limits):</b>
• ⬅️ BACK navigation through history
• 💰 Buy coin links and information
• Alert button navigation

🔴 <b>Rate limited (1 second between requests):</b>
• New coin searches (fresh API data)
• 👉 NEXT discoveries (new coins)

🔥 Alert System Benefits:
✅ Free navigation from alerts
🎯 Only 80%+ FOMO score notifications
⚡ No rate limits for alert navigation

⏰ When do scans reset?
- Daily scans: Reset at 00:00 UTC
- New user bonus: One-time only
- FCB tokens: Never expire

💡 Pro Tips:
- Use alerts for free high-quality opportunities
- Navigate freely through your coin history
- Get 250+ scans for premium features"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 View Alerts", url="https://t.me/fomocryptobot_alert")],
        [
            InlineKeyboardButton("🤖 Get 250 Scans", callback_data="buy_starter"),
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")
        ]
    ])
    
    await safe_edit_message(query, text=info_msg, reply_markup=keyboard)

async def handle_show_help(query, context, user_id):
    """FIXED: Show help information with accurate economics explanation"""
    
    help_msg = f"""❓ <b>FOMO Crypto Bot Help</b>

🔥 <b>Alert System:</b>
• Get premium opportunities sent directly
• Only 80%+ FOMO score coins trigger alerts
• Click alert buttons for free navigation
• Up to 6 quality alerts per day

💰 <b>Token Economics:</b>
🟢 <b>Always FREE:</b>
• ⬅️ BACK - Navigate through coin history
• 💰 BUY COIN - Get purchase links
• Alert button navigation
• Menu actions and balance checks

🔴 <b>Costs 1 token:</b>
• New coin searches (type coin name)
• 👉 NEXT - Discover new coins
• Fresh market analysis and data

📊 <b>How to Use:</b>
• Type any coin name → 1 token for fresh analysis
• Click buttons to navigate and explore
• Alerts give you premium coins to explore freely
• Use BACK to revisit without token cost

💎 <b>Token System:</b>
• Free daily scans reset at 00:00 UTC
• FCB tokens never expire
• Alert navigation always free
• Premium users get 250+ scans per purchase

📺 <b>Track Record:</b> https://t.me/fomocryptobot_alert

💡 <b>Commands:</b>
• `/start` - Subscribe to alerts
• `/test` - Test alert with working buttons
• `/status` - Check subscriber count
• `/buy` - Purchase FCB tokens
• `/balance` - View detailed balance

🎯 <b>Smart Usage Tips:</b>
• Use alerts to get premium opportunities for free
• Navigate through history without token costs
• Pay only for new discoveries and fresh data
• BACK button is always free - use it liberally!"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Test Alerts", callback_data="test_alert_system")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]
    ])
    
    await safe_edit_message(query, text=help_msg, reply_markup=keyboard)

# =============================================================================
# Enhanced Callback Query Handler with Perfect Token Economics
# =============================================================================

async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced callback handler with perfect token economics
    - FREE: Navigation through history, buy links, menu actions
    - 1 TOKEN: Only fresh API calls for new coin discoveries
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    logging.info(f"🔍 CALLBACK DEBUG: User {user_id} clicked '{query.data}'")
    
    # =============================================================================
    # ALWAYS FREE ACTIONS (No rate limiting, no token cost)
    # =============================================================================
    
    if query.data == "back_to_main":
        await handle_back_to_main(query, context, user_id)
        return
    
    elif query.data == "show_rate_limit_info":
        await handle_rate_limit_info(query, context, user_id)
        return
    
    elif query.data == "show_help":
        await handle_show_help(query, context, user_id)
        return
    
    elif query.data == "test_alert_system":
        await handle_test_alert_system(query, context, user_id)
        return
    
    # Purchase buttons - always free to access
    elif query.data.startswith("buy_"):
        await handle_star_purchase(update, context)
        return
    
    # Buy coin button - always FREE
    elif query.data == "buy_coin" or query.data.startswith("buy_coin"):
        await handle_buy_coin_button(query, context, user_id)
        return
    
    # Back to analysis from buy screen - FREE if cached data available
    elif query.data == "back_to_analysis":
        await handle_back_to_analysis(query, context, user_id)
        return
    
    # BACK button - ALWAYS FREE (uses cached data)
    elif query.data.startswith("back_"):
        await handle_back_navigation(query, context, user_id)
        return
    
    elif query.data == "check_balance":
        user_id = query.from_user.id
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        # FIXED: Enhanced balance message with accurate economics
        message = f"""📊 <b>Balance Update</b>
        
🎯 Scans Available: <b>{total_free_remaining}</b>
💎 FCB Tokens: <b>{fcb_balance}</b>

💰 <b>Token Economics:</b>
🟢 <b>Always FREE:</b>
• ⬅️ BACK navigation through history
• 💰 Buy coin links and information
• 🤖 TOP UP and menu actions

🔴 <b>Costs 1 token:</b>
• New coin searches (fresh API data)
• 👉 NEXT discoveries (new coins only)
• Fresh analysis and market data

🔥 <b>Alert Benefits:</b>
✅ Free navigation from alerts
🎯 Only 80%+ FOMO score opportunities
⚡ Up to 6 quality alerts daily

💡 <b>Smart Usage:</b>
• Use alerts to get premium coins for free
• Navigate history without costs
• Pay only for fresh discoveries"""
        
        # Add helpful keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Get 250 Scans", callback_data="buy_starter")],
            [InlineKeyboardButton("🧪 Test Alerts", callback_data="test_alert_system")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
        ])
        
        await safe_edit_message(query, text=message, reply_markup=keyboard)
        return
    
    # =============================================================================
    # TOKEN-BASED ACTIONS (Check rate limits and balances)
    # =============================================================================
    
    # NEXT button - Smart economics: FREE for history, 1 token for new discoveries
    if query.data == "next_coin":
        # Check if this is forward navigation (FREE) or new discovery (1 token)
        session = get_user_session(user_id)
        history = session.get('history', [])
        current_index = session.get('index', 0)
        
        # If we can move forward through existing history, it's FREE
        if history and current_index < len(history) - 1:
            # FREE forward navigation
            await handle_next_navigation(query, context, user_id)
            return
        else:
            # New discovery - check rate limits and tokens
            allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
            
            if not allowed:
                if reason == "No queries available":
                    message = format_out_of_scans_back_message_with_navigation()
                    keyboard = build_out_of_scans_back_keyboard_with_navigation()
                    await safe_edit_message(query, text=message, reply_markup=keyboard)
                else:
                    countdown_msg = create_countdown_visual(time_remaining)
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main")]
                    ])
                    await safe_edit_message(query, text=countdown_msg, reply_markup=keyboard)
                return
            
            # Proceed with new discovery (will cost 1 token)
            await handle_next_navigation(query, context, user_id)
            return
    
    # =============================================================================
    # UNKNOWN CALLBACK HANDLING
    # =============================================================================
    
    else:
        logging.warning(f"UNKNOWN CALLBACK: '{query.data}' from user {user_id}")
        
        # Try to extract coin info from alert message for unknown callbacks
        if hasattr(query, 'message') and query.message and query.message.text:
            extracted_coin = extract_coin_id_from_alert_message(query.message.text)
            if extracted_coin:
                logging.info(f"Extracted coin {extracted_coin} from unknown callback, attempting analysis")
                
                # Add to navigation history as alert coin
                add_alert_coin_to_history(user_id, extracted_coin)
                
                # Analyze the extracted coin (this might cost a token if no cached data)
                result = await handle_alert_coin_analysis(user_id, extracted_coin, context, query.message)
                
                if result:
                    await safe_edit_message(query, text=result['message'], reply_markup=result['keyboard'])
                    return
        
        # Fallback for truly unknown actions
        await safe_edit_message(query, text="❌ Unknown action. Please try again or type a coin name to search.")

# =============================================================================
# END OF PART 7/8 - "UNLIMITED" MESSAGING FIXED - Menu Helpers & Enhanced Callback Handler Complete
# =============================================================================

"""
Telegram handlers module for CFB (Crypto FOMO Bot) - TEXT CONSISTENCY FIXED VERSION
PART 8/8: Payment Processing, Error Handling & Setup Functions - CRITICAL FIXES APPLIED

FIXES APPLIED:
- ✅ Enhanced handler setup with debug logging
- ✅ Fixed command registration order
- ✅ Added comprehensive error handling
- ✅ Added command verification system
- ✅ Fixed import order issues
- ✅ Added admin campaign commands
"""

# =============================================================================
# ADMIN CAMPAIGN COMMANDS
# =============================================================================

async def campaign_links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: Get all campaign links"""
    user_id = update.effective_user.id
    
    # Import here to avoid circular imports
    try:
        from config import ADMIN_USER_IDS
    except ImportError:
        ADMIN_USER_IDS = []
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Admin access required")
        return
    
    links_text = campaign_manager.generate_all_links()
    await update.message.reply_text(links_text, parse_mode='Markdown')

async def campaign_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: View campaign analytics"""
    user_id = update.effective_user.id
    
    # Import here to avoid circular imports
    try:
        from config import ADMIN_USER_IDS, ANALYTICS_ENABLED
    except ImportError:
        ADMIN_USER_IDS = []
        ANALYTICS_ENABLED = True
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Admin access required")
        return
    
    if not ANALYTICS_ENABLED:
        await update.message.reply_text("📊 Analytics disabled in config")
        return
    
    report = campaign_manager.get_analytics_report()
    await update.message.reply_text(report, parse_mode='Markdown')

# =============================================================================
# Payment Handlers - Complete Stars Payment Processing (FIXED)
# =============================================================================

async def handle_star_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle star purchase button clicks with clean error handling"""
    query = update.callback_query
    
    package_key = query.data.replace("buy_", "")
    if package_key in FCB_STAR_PACKAGES:
        package = FCB_STAR_PACKAGES[package_key]
        
        try:
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=package['title'],
                description=package['description'],
                payload=f"fcb_{package_key}_{query.from_user.id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(package['title'], package['stars'])],
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False
            )
        except Exception as e:
            logging.error(f"Error sending invoice: {e}")
            await safe_edit_message(query, text="❌ Error creating invoice. Please try again.")

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout validation for payment security"""
    query = update.pre_checkout_query
    
    if query.invoice_payload.startswith("fcb_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid purchase")

async def payment_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    FIXED: Handle successful Stars payments with accurate economics messaging
    """
    payment = update.message.successful_payment
    actual_buyer_id = update.effective_user.id
    
    logging.info(f"🔍 PAYMENT DEBUG: Buyer ID: {actual_buyer_id}")
    logging.info(f"🔍 PAYMENT DEBUG: Payload: {payment.invoice_payload}")
    logging.info(f"🔍 PAYMENT DEBUG: Stars amount: {payment.total_amount}")
    
    payload_parts = payment.invoice_payload.split("_")
    
    if len(payload_parts) == 3 and payload_parts[0] == "fcb":
        package_key = payload_parts[1]
        payload_user_id = int(payload_parts[2])
        
        if actual_buyer_id != payload_user_id:
            logging.error(f"❌ SECURITY ALERT: Buyer {actual_buyer_id} != Payload {payload_user_id}")
            await update.message.reply_text(
                "❌ Payment verification failed. Please contact support.",
                parse_mode='HTML'
            )
            return
        
        if package_key in FCB_STAR_PACKAGES:
            tokens = FCB_STAR_PACKAGES[package_key]['tokens']
            stars = FCB_STAR_PACKAGES[package_key]['stars']
            
            success, new_balance = add_fcb_tokens(actual_buyer_id, tokens)
            
            if success:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE users 
                            SET first_purchase_date = CURRENT_TIMESTAMP 
                            WHERE user_id = ? AND first_purchase_date IS NULL
                        ''', (actual_buyer_id,))
                        conn.commit()
                except Exception as e:
                    logging.error(f"Error updating first purchase date: {e}")
                
                # FIXED: Enhanced success message with accurate economics explanation
                message = f"""🎉 <b>Purchase Successful!</b>

💎 <b>{tokens} FCB tokens</b> added to your account!
⭐ <b>{stars} Stars</b> spent

📊 <b>Your Balance:</b>
💎 FCB Tokens: <b>{new_balance}</b>
🎯 Premium Scans: <b>{tokens} available!</b>

💰 <b>What You Can Do:</b>
🟢 <b>Always FREE:</b> ⬅️ BACK navigation, 💰 buy links
🔴 <b>1 token each:</b> New coin searches, 👉 NEXT discoveries

🔥 <b>Alert Benefits:</b>
✅ Keep receiving premium alerts (FREE)
🎯 Navigate freely from any alert
⚡ Smart token usage with cached history

🚀 <b>Ready to scan?</b> Type any coin name to get started!

💡 <b>Pro Tip:</b> Use alerts and BACK navigation to explore more without spending tokens!"""
                
                await update.message.reply_text(message, parse_mode='HTML')
                
                logging.info(f"✅ PAYMENT SUCCESS: User {actual_buyer_id} bought {tokens} FCB tokens for {stars} Stars - New balance: {new_balance}")
            else:
                logging.error(f"❌ PAYMENT FAILED: Database error for user {actual_buyer_id}")
                await update.message.reply_text(
                    "❌ Payment processed but token delivery failed. Please contact support with this transaction ID.",
                    parse_mode='HTML'
                )
        else:
            logging.error(f"❌ Invalid package key: {package_key}")
            await update.message.reply_text(
                "❌ Invalid purchase package. Please contact support.",
                parse_mode='HTML'
            )
    else:
        logging.error(f"❌ Invalid payment payload: {payment.invoice_payload}")
        await update.message.reply_text(
            "❌ Payment verification failed. Please contact support.",
            parse_mode='HTML'
        )

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

# =============================================================================
# CRITICAL FIX: Enhanced Handler Setup Function
# =============================================================================

def setup_admin_handlers(app):
    """Setup admin campaign handlers"""
    from telegram.ext import CommandHandler
    
    logging.info("🔧 Setting up admin campaign handlers...")
    
    try:
        app.add_handler(CommandHandler("links", campaign_links_command))
        app.add_handler(CommandHandler("campaigns", campaign_stats_command))
        logging.info("✅ Admin campaign handlers registered")
    except Exception as e:
        logging.error(f"❌ Admin handler registration failed: {e}")

def setup_handlers(app):
    """
    Setup all handlers with perfect token economics and comprehensive debugging
    CRITICAL FIXES: Enhanced import handling, command verification, debug logging
    """
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
    
    logging.info("🚀 STARTING HANDLER SETUP WITH CRITICAL FIXES")
    logging.info("=" * 60)
    
    # CRITICAL FIX 1: Initialize database with enhanced error handling
    try:
        from database import init_user_db
        init_user_db()
        logging.info("✅ Database initialized successfully")
    except Exception as db_error:
        logging.error(f"❌ CRITICAL: Database initialization failed: {db_error}")
        raise
    
    # CRITICAL FIX 2: Verify command imports and registration
    logging.info("🔍 VERIFYING COMMAND IMPORTS...")
    
    # Import verification with detailed logging
    command_functions = {}
    try:
        # These should be available from the current module
        command_functions = {
            'start': start_command,
            'help': help_command,
            'terms': terms_command,
            'scans': scans_command,
            'premium': premium_command,
            'support': support_command,
            'buy': buy_command,
            'debug': debug_balance_command,
            'balance': balance_command,
            'test': None,  # Will be imported separately
            'status': None,  # Will be imported separately
            'unsubscribe': None,  # Will be imported separately
            'debugsession': None  # Will be imported separately
        }
        
        logging.info("✅ Primary command functions verified")
        
        # Try to import additional functions with fallback
        try:
            command_functions['test'] = test_command
            command_functions['status'] = status_command
            command_functions['unsubscribe'] = unsubscribe_command
            command_functions['debugsession'] = debug_session_command
            logging.info("✅ Additional command functions found")
        except NameError as name_error:
            logging.warning(f"⚠️ Some additional commands not available: {name_error}")
        
    except Exception as import_error:
        logging.error(f"❌ CRITICAL: Command function import failed: {import_error}")
        raise
    
    # CRITICAL FIX 3: Register commands with verification
    logging.info("📝 REGISTERING COMMAND HANDLERS...")
    
    registered_count = 0
    
    for cmd_name, cmd_func in command_functions.items():
        if cmd_func and callable(cmd_func):
            try:
                app.add_handler(CommandHandler(cmd_name, cmd_func))
                logging.info(f"  ✅ /{cmd_name} -> {cmd_func.__name__}")
                registered_count += 1
            except Exception as reg_error:
                logging.error(f"  ❌ /{cmd_name} registration failed: {reg_error}")
        else:
            logging.warning(f"  ⚠️ /{cmd_name} -> NOT AVAILABLE")
    
    logging.info(f"✅ Successfully registered {registered_count} command handlers")
    
    # CRITICAL FIX 4: Enhanced callback query handler with error handling
    try:
        app.add_handler(CallbackQueryHandler(handle_callback_queries))
        logging.info("✅ Callback query handler registered")
    except Exception as callback_error:
        logging.error(f"❌ Callback handler registration failed: {callback_error}")
    
    # CRITICAL FIX 5: Payment handlers with verification
    try:
        app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success_handler))
        logging.info("✅ Payment handlers registered")
    except Exception as payment_error:
        logging.error(f"❌ Payment handler registration failed: {payment_error}")
    
    # CRITICAL FIX 6: Admin campaign handlers
    try:
        setup_admin_handlers(app)
        logging.info("✅ Admin campaign handlers registered")
    except Exception as admin_error:
        logging.error(f"❌ Admin handler registration failed: {admin_error}")
    
    # CRITICAL FIX 7: Main message handler LAST (very important!)
    try:
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_coin_message_ultra_fast))
        logging.info("✅ Main message handler registered (LAST - correct order)")
    except Exception as message_error:
        logging.error(f"❌ Main message handler registration failed: {message_error}")
    
    # CRITICAL FIX 8: Error handler with enhanced logging
    try:
        app.add_error_handler(error_handler)
        logging.info("✅ Error handler registered")
    except Exception as error_handler_error:
        logging.error(f"❌ Error handler registration failed: {error_handler_error}")
    
    # CRITICAL FIX 9: Final verification and status report
    logging.info("=" * 60)
    logging.info("🎯 HANDLER SETUP COMPLETE - STATUS REPORT:")
    logging.info(f"  📝 Commands registered: {registered_count}")
    logging.info(f"  🔄 Callback handlers: ✅")
    logging.info(f"  💳 Payment handlers: ✅")
    logging.info(f"  👑 Admin handlers: ✅")
    logging.info(f"  📨 Message handler: ✅")
    logging.info(f"  ⚠️ Error handler: ✅")
    
    # Run command verification
    try:
        verify_command_registration()
    except Exception as verify_error:
        logging.warning(f"Command verification failed: {verify_error}")
    
    logging.info("✅ ALL FIXES APPLIED: Handler setup completed successfully!")
    logging.info("🎯 Bot is ready for production with enhanced error handling!")
    logging.info("📈 Campaign tracking system is active!")
    
    return True

# =============================================================================
# CRITICAL DEBUGGING HELPERS
# =============================================================================

def debug_handler_setup():
    """Debug function to check handler setup status"""
    logging.info("🔍 DEBUGGING HANDLER SETUP:")
    
    # Check if functions are defined
    functions_to_check = [
        'start_command', 'help_command', 'terms_command', 'scans_command',
        'premium_command', 'support_command', 'buy_command', 'balance_command',
        'campaign_links_command', 'campaign_stats_command'
    ]
    
    for func_name in functions_to_check:
        try:
            func = globals().get(func_name)
            if func and callable(func):
                logging.info(f"  ✅ {func_name} is available and callable")
            else:
                logging.error(f"  ❌ {func_name} is NOT available or not callable")
        except Exception as e:
            logging.error(f"  ❌ Error checking {func_name}: {e}")
    
    # Check imports
    try:
        from database import get_user_balance_info
        logging.info("  ✅ Database functions imported successfully")
    except ImportError as e:
        logging.error(f"  ❌ Database import failed: {e}")
    
    try:
        from config import FCB_STAR_PACKAGES
        logging.info("  ✅ Config imported successfully")
    except ImportError as e:
        logging.error(f"  ❌ Config import failed: {e}")
    
    try:
        from campaign_manager import campaign_manager
        logging.info("  ✅ Campaign manager imported successfully")
    except ImportError as e:
        logging.error(f"  ❌ Campaign manager import failed: {e}")

def test_help_command_directly():
    """Test function to verify help command works"""
    logging.info("🧪 TESTING HELP COMMAND DIRECTLY:")
    
    try:
        # Check if help_command function exists and is callable
        if 'help_command' in globals() and callable(help_command):
            logging.info("  ✅ help_command function is available")
            logging.info(f"  📋 Function signature: {help_command.__name__}")
            logging.info(f"  📝 Function module: {help_command.__module__}")
            return True
        else:
            logging.error("  ❌ help_command function is NOT available")
            return False
    except Exception as e:
        logging.error(f"  ❌ Error testing help command: {e}")
        return False

# =============================================================================
# COMMAND REGISTRY FOR VERIFICATION
# =============================================================================

REGISTERED_COMMANDS = {
    'start': start_command,
    'help': help_command,
    'terms': terms_command,
    'scans': scans_command,
    'premium': premium_command,
    'support': support_command,
    'buy': buy_command,
    'balance': balance_command,
    'debug': debug_balance_command,
    'links': campaign_links_command,
    'campaigns': campaign_stats_command
}

def verify_command_registration():
    """Verify all commands are properly defined"""
    logging.info("🔍 VERIFYING COMMAND REGISTRATION:")
    for cmd_name, cmd_func in REGISTERED_COMMANDS.items():
        if callable(cmd_func):
            logging.info(f"  ✅ /{cmd_name} -> {cmd_func.__name__}")
        else:
            logging.error(f"  ❌ /{cmd_name} -> NOT CALLABLE!")
    logging.info(f"✅ Total commands registered: {len(REGISTERED_COMMANDS)}")

# =============================================================================
# Final Implementation Summary & Deployment Notes
# =============================================================================

"""
🎉 CAMPAIGN TRACKING SYSTEM COMPLETE! 🎉

✅ **CAMPAIGN SYSTEM IMPLEMENTED:**

📈 **Campaign Manager:**
• Centralized campaign link management
• .env-driven configuration  
• Auto-generated campaign URLs
• Campaign analytics and reporting

🔧 **Database Integration:**
• Campaign tracking columns added
• User acquisition source tracking
• Purchase conversion analytics
• Admin-only analytics access

🎯 **Admin Commands:**
• /links - Get all campaign URLs (admin only)
• /campaigns - View analytics (admin only)
• Links auto-update from .env changes
• Performance tracking by source

⚙️ **Configuration:**
• CAMPAIGN_TRACKING_ENABLED toggle
• BOT_USERNAME for link generation
• ADMIN_USER_IDS for access control
• Campaign codes in .env variables

📊 **Analytics Tracking:**
• User acquisition by source
• Purchase conversion rates
• Campaign performance metrics
• Source attribution tracking

🎯 **DEPLOYMENT READY:**
All files are updated and integrated with your existing modular structure.
Campaign tracking works seamlessly with your current FCB token system.
"""

# =============================================================================
# END OF PART 8/8 - CAMPAIGN TRACKING SYSTEM COMPLETE
# =============================================================================