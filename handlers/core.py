"""
handlers/core.py - Core Session Management, Utilities & Setup
All essential functions needed by other handler modules
"""

import logging
import random
import asyncio
import time 
from datetime import datetime 
from io import BytesIO

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
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
    get_db_connection,
    init_user_db
)

# Core imports
from config import FCB_STAR_PACKAGES, INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, FOMO_CACHE
from api_client import get_coin_info_ultra_fast, get_optimized_session
from analysis import calculate_fomo_status_ultra_fast

# Campaign imports
from campaign_manager import campaign_manager, format_campaign_welcome

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
# Session Management with Cached Data Storage
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
            'cached_data': {},
            'from_alert': False
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
    """Add coin to user's navigation history with cached data"""
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
        
        # Cache the coin data for FREE navigation
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
    """Get cached coin data for FREE navigation"""
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
# Clean Opportunity Hunter
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
    """Clean opportunity hunting without noisy excitement messages"""
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
    """Get simple, clean balance display"""
    try:
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        total_scans = total_free_remaining + fcb_balance
        return f"🤖 <i>Tokens: {total_scans}</i>"
    except Exception as e:
        logging.error(f"Error getting clean balance: {e}")
        return "🤖 <i>Tokens: Error</i>"

def get_user_balance_info(user_id):
    """Get complete user balance info for internal use"""
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
# Safe Message Editing
# =============================================================================

async def safe_edit_message(query, text=None, caption=None, reply_markup=None, parse_mode='HTML'):
    """Safely edit a message, handling alert messages and all edge cases"""
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
# Debug Helper Functions
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
# CRITICAL: Handler Setup Function
# =============================================================================

def setup_handlers(app):
    """Setup all handlers with perfect token economics"""
    logging.info("🚀 STARTING HANDLER SETUP")
    logging.info("=" * 60)
    
# Initialize database
    try:
        init_user_db()
        logging.info("✅ Database initialized successfully")
    except Exception as db_error:
        logging.error(f"❌ CRITICAL: Database initialization failed: {db_error}")
        raise
    
    # Import all handler modules
    try:
        # Import core commands
        from .commands import (
            start_command, help_command, terms_command, scans_command,
            premium_command, support_command, buy_command, balance_command,
            debug_balance_command
        )
        # Import utility commands
        from .utils import (
            test_command, status_command, unsubscribe_command,
            debug_session_command
        )
        from .campaigns import campaign_links_command, campaign_stats_command
        from .discovery import send_coin_message_ultra_fast
        from .callbacks import handle_callback_queries
        from .payments import pre_checkout_handler, payment_success_handler
        from .errors import error_handler
        
        logging.info("✅ All handler modules imported successfully")
    except Exception as import_error:
        logging.error(f"❌ CRITICAL: Handler import failed: {import_error}")
        raise
    
    # Register command handlers
    command_handlers = {
        'start': start_command,
        'help': help_command,
        'terms': terms_command,
        'scans': scans_command,
        'premium': premium_command,
        'support': support_command,
        'buy': buy_command,
        'balance': balance_command,
        'debug': debug_balance_command,
        'test': test_command,
        'status': status_command,
        'unsubscribe': unsubscribe_command,
        'debugsession': debug_session_command,
        'links': campaign_links_command,
        'campaigns': campaign_stats_command
    }
    
    registered_count = 0
    for cmd_name, cmd_func in command_handlers.items():
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
    
    # Register callback query handler
    try:
        app.add_handler(CallbackQueryHandler(handle_callback_queries))
        logging.info("✅ Callback query handler registered")
    except Exception as callback_error:
        logging.error(f"❌ Callback handler registration failed: {callback_error}")
    
    # Register payment handlers
    try:
        app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success_handler))
        logging.info("✅ Payment handlers registered")
    except Exception as payment_error:
        logging.error(f"❌ Payment handler registration failed: {payment_error}")
    
    # Register main message handler LAST (very important!)
    try:
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_coin_message_ultra_fast))
        logging.info("✅ Main message handler registered (LAST - correct order)")
    except Exception as message_error:
        logging.error(f"❌ Main message handler registration failed: {message_error}")
    
    # Register error handler
    try:
        app.add_error_handler(error_handler)
        logging.info("✅ Error handler registered")
    except Exception as error_handler_error:
        logging.error(f"❌ Error handler registration failed: {error_handler_error}")
    
    # Final status report
    logging.info("=" * 60)
    logging.info("🎯 HANDLER SETUP COMPLETE - STATUS REPORT:")
    logging.info(f"  📝 Commands registered: {registered_count}")
    logging.info(f"  🔄 Callback handlers: ✅")
    logging.info(f"  💳 Payment handlers: ✅")
    logging.info(f"  📨 Message handler: ✅")
    logging.info(f"  ⚠️ Error handler: ✅")
    logging.info("✅ Bot is ready for production!")
    
    return True