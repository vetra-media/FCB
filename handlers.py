"""
Telegram handlers module for CFB (Crypto FOMO Bot)
Handles all Telegram bot interactions, commands, and callbacks
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
from config import FCB_STAR_PACKAGES, INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, FOMO_CACHE
from api_client import get_coin_info_ultra_fast, get_optimized_session
from analysis import calculate_fomo_status_ultra_fast
from formatters import (
    format_fomo_message, format_treasure_discovery_message, format_balance_message,
    format_purchase_options_message, format_out_of_scans_message, 
    format_out_of_scans_back_message, format_payment_success_message,
    format_out_of_scans_message_with_back, format_out_of_scans_back_message_with_navigation,
    build_addictive_buttons, build_purchase_keyboard, build_out_of_scans_keyboard,
    build_out_of_scans_back_keyboard, build_out_of_scans_keyboard_with_back,
    build_out_of_scans_back_keyboard_with_navigation, create_countdown_visual,
    get_start_message, get_help_message
)
from cache import get_ultra_fast_fomo_opportunities
from scanner import add_user_to_notifications, subscribed_users, save_subscriptions

user_sessions = {}  # {user_id: {'history': [], 'index': 0, 'last_activity': timestamp}}

def validate_coingecko_id(coin_id):
    """Validate CoinGecko ID format - CRITICAL VALIDATION FROM YOUR RECENT FIX"""
    if not coin_id or not isinstance(coin_id, str):
        return False
    
    # Remove common invalid patterns that crash the API
    invalid_patterns = [
        'unknown', '', None, 'null', 'undefined',
        'jerry-the-turtle-by-matt-furie',  # Your example of problematic ID
        'agenda-47'  # Your example of problematic ID
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

def get_user_session(user_id):
    """Get or create user-specific session"""
    current_time = time.time()
    
    # Clean old sessions (older than 24 hours)
    cleanup_old_sessions(current_time)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'history': [],
            'index': 0,
            'last_activity': current_time
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

def add_to_user_history(user_id, coin_id):
    """Add coin to user's navigation history"""
    session = get_user_session(user_id)
    
    # Only add if it's different from the last coin (avoid duplicates)
    if not session['history'] or session['history'][-1] != coin_id:
        session['history'].append(coin_id)
        # Set index to newest coin
        session['index'] = len(session['history']) - 1
        logging.info(f"User {user_id}: Added {coin_id} to history at position {session['index']}")
    
    return session

def debug_user_session(user_id, context=""):
    """Debug function to log user session state"""
    if user_id in user_sessions:
        session = user_sessions[user_id]
        logging.info(f"🔍 SESSION DEBUG for User {user_id} ({context}):")
        logging.info(f"  History: {session['history']}")
        logging.info(f"  Index: {session['index']}")
        logging.info(f"  History length: {len(session['history'])}")
        
        if session['history'] and 0 <= session['index'] < len(session['history']):
            logging.info(f"  Current coin: {session['history'][session['index']]}")
        else:
            logging.info(f"  ❌ Index out of bounds!")
    else:
        logging.info(f"🔍 SESSION DEBUG: User {user_id} has no session")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def safe_edit_message(query, text=None, caption=None, reply_markup=None, parse_mode='HTML'):
    """
    Safely edit a message, handling all edge cases including photo messages
    """
    try:
        # Try to edit message text first
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
                
                # If no text to edit, try editing caption
                if "no text in the message to edit" in error_msg:
                    try:
                        await query.edit_message_caption(
                            caption=text,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup
                        )
                        return True
                    except Exception:
                        pass  # Will fall back to delete+send
                
                # If message can't be edited, delete and send new
                try:
                    await query.message.delete()
                except Exception:
                    pass  # Message might already be deleted
                
                # Send new message
                await query.message.chat.send_message(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                return True
        
        # Handle caption editing
        elif caption is not None:
            try:
                await query.edit_message_caption(
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
                return True
            except Exception:
                # Fallback to delete and send
                try:
                    await query.message.delete()
                except Exception:
                    pass
                
                await query.message.chat.send_message(
                    text=caption,
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
# COMMAND HANDLERS
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Subscribe user to notifications
    add_user_to_notifications(user_id)
    
    logging.info(f"User {username} (ID: {user_id}) subscribed to FOMO alerts")
    
    message = f"""👋 Welcome to <b>Fomo Crypto Bot</b>!

✅ **Type any coin name in chat to start the bot e.g. bitcoin**

- 🎰 NEXT for new opportunities 
- ⬅️ BACK through previous coins
- 💰 BUY where to buy coins
- ⭐ TOP UP for more scans

📺 See our public track record: https://t.me/fomocryptobot_alert
📋 T&C's in pin @freecryptopings

💡 **New Commands:**
- `/test` - Test your notification subscription
- `/status` - Check your balance and status"""
    
    await update.message.reply_text(message, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message = get_help_message()
    await update.message.reply_text(message, parse_mode='HTML')

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command - Show FCB token purchase options"""
    user_id = update.effective_user.id
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    user_balance_info = {
        'fcb_balance': fcb_balance,
        'free_queries_used': free_queries_used,
        'new_user_bonus_used': new_user_bonus_used,
        'total_free_remaining': total_free_remaining,
        'has_received_bonus': has_received_bonus
    }
    
    message = format_purchase_options_message(user_balance_info)
    keyboard = build_purchase_keyboard()
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - Show detailed balance with conversion hooks"""
    user_id = update.effective_user.id
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    user_balance_info = {
        'fcb_balance': fcb_balance,
        'free_queries_used': free_queries_used,
        'new_user_bonus_used': new_user_bonus_used,
        'total_free_remaining': total_free_remaining,
        'has_received_bonus': has_received_bonus
    }
    
    message = format_balance_message(user_balance_info, conversion_hooks=True)
    await update.message.reply_text(message, parse_mode='HTML')

async def debug_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check detailed balance information"""
    user_id = update.effective_user.id
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

🎯 <b>Available Scans:</b> {balance_info['total_free_remaining']} free + {balance_info['fcb_balance']} tokens"""
    else:
        message = "❌ Could not retrieve balance information."
    
    await update.message.reply_text(message, parse_mode='HTML')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test notification to verify the user notification system"""
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
    
    # Create test data that mimics a real FOMO alert
    test_data = {
        'id': 'test-coin',
        'name': 'TEST COIN',
        'symbol': 'TEST',
        'price': 0.001234,
        'change_1h': 12.5,
        'change_24h': 156.78,
        'volume': 9876543,
        'logo': None
    }
    
    # Format the test message using your existing formatter
    from formatters import format_fomo_message
    message_text = format_fomo_message(test_data, 95, "🚀 MOON SHOT", True, "Bullish", "Whale Activity", is_broadcast=False)
    
    # Add test indicator
    test_message = "🧪 **TEST ALERT** 🧪\n\n" + message_text + "\n\n*This is a test notification to verify your subscription is working!*"
    
    # Create interactive buttons using your existing function
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
            "✅ Test notification sent! Check above for the test alert with working buttons.",
            parse_mode='HTML'
        )
        
        logging.info(f"Test notification sent successfully to {username} (ID: {user_id})")
        
    except Exception as e:
        logging.error(f"Failed to send test notification to {username} (ID: {user_id}): {e}")
        await update.message.reply_text(
            "❌ Failed to send test notification. Please try again or contact support.",
            parse_mode='HTML'
        )

async def debug_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check user session state"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        message = f"""🔍 <b>Session Debug for User {user_id}</b>

📊 <b>Current State:</b>
History Length: {len(session['history'])}
Current Index: {session['index']}
History: {session['history']}

🎯 <b>Current Coin:</b> {session['history'][session['index']] if session['history'] and 0 <= session['index'] < len(session['history']) else 'Invalid'}

🕒 <b>Session Info:</b>
Last Activity: {datetime.fromtimestamp(session['last_activity']).strftime('%Y-%m-%d %H:%M:%S')}

📈 <b>Navigation:</b>
Can go back: {session['index'] > 0}
Can go forward: {session['index'] < len(session['history']) - 1}

<i>Check logs for detailed debug info</i>"""
    else:
        message = f"🔍 <b>Session Debug</b>\n\nUser {user_id} has no active session."
    
    await update.message.reply_text(message, parse_mode='HTML')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status and subscriber count"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    subscriber_count = len(subscribed_users)
    
    status_message = f"""📊 **FOMO Bot Status**

👥 **Subscribers:** {subscriber_count}
🔄 **Your Status:** {'✅ Subscribed' if user_id in subscribed_users else '❌ Not Subscribed'}

📺 **Channel:** https://t.me/fomocryptobot_alert
🤖 **Bot:** @fomocryptobot

💡 **Commands:**
- `/start` - Subscribe to alerts  
- `/test` - Test notifications
- `/status` - Show this status
- `/unsubscribe` - Stop alerts
- `/buy` - Purchase FCB tokens
- `/balance` - Check your balance"""

    await update.message.reply_text(status_message, parse_mode='HTML')
    logging.info(f"Status command used by {username} (ID: {user_id})")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to unsubscribe from FOMO alerts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        from scanner import save_subscriptions
        save_subscriptions()
        await update.message.reply_text("🛑 You've been unsubscribed from FOMO alerts.", parse_mode='HTML')
        logging.info(f"User {username} (ID: {user_id}) unsubscribed from FOMO alerts")
    else:
        await update.message.reply_text("ℹ️ You are not currently subscribed.", parse_mode='HTML')

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command"""
    message = """📋 <b>Terms & Disclaimer</b>
    
⚖️ <b>Full Terms:</b> @freecryptopings (see pinned message)
    
🚨 <b>Key Points:</b>
- High risk - you could lose everything  
- 100% FOMO ≠ 100% success
- Must be 18+ and legally able to trade crypto
- We earn via Stars + affiliate links

<i>By using this bot, you accept these terms.</i>"""
    
    await update.message.reply_text(message, parse_mode='HTML')

# =============================================================================
# ULTRA-FAST MESSAGE HANDLERS
# =============================================================================

async def handle_instant_spin(query, context, user_id):
    """Handle the 'NEXT' button with instant treasure discovery - FIXED COINGECKO ID VALIDATION"""
    
    # Spend the query first
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        await safe_edit_message(query, text=spend_message)
        return
    
    # INSTANT visual feedback
    instant_msg = random.choice(INSTANT_SPIN_RESPONSES)
    await safe_edit_message(query, text=f"🎰 <b>{instant_msg}</b>")
    
    try:
        # Check if we have cached opportunities
        from config import FOMO_CACHE
        if not FOMO_CACHE['coins'] or not FOMO_CACHE['coins']:
            # Fallback to live search if cache is empty
            await safe_edit_message(query, text="🔍 <b>Searching for fresh opportunities...</b>")
            
            # Quick scan for opportunities
            from cache import get_ultra_fast_fomo_opportunities
            opportunities = await get_ultra_fast_fomo_opportunities()
            if opportunities:
                FOMO_CACHE['coins'] = opportunities
                FOMO_CACHE['current_index'] = 0
        
        if FOMO_CACHE['coins']:
            # Get next coin from cache
            current_index = FOMO_CACHE.get('current_index', 0)
            if current_index >= len(FOMO_CACHE['coins']):
                FOMO_CACHE['current_index'] = 0
                current_index = 0
            
            coin_data = FOMO_CACHE['coins'][current_index]
            FOMO_CACHE['current_index'] = current_index + 1
            
            # Convert cached data to coin format
            coin = {
                'id': coin_data.get('coin', coin_data.get('id', 'unknown')),
                'name': coin_data.get('name', 'Unknown'),
                'symbol': coin_data.get('symbol', ''),
                'logo': coin_data.get('logo') or coin_data.get('image'),
                'price': coin_data.get('current_price', coin_data.get('price', 0)),
                'change_1h': coin_data.get('price_1h_change (%)', coin_data.get('change_1h', 0)),
                'change_24h': coin_data.get('price_24h_change (%)', coin_data.get('change_24h', 0)),
                'volume': coin_data.get('volume_24h', coin_data.get('volume', 0)),
                'source_url': coin_data.get('source_url', 'https://coingecko.com')
            }
            
            # 🔧 CRITICAL FIX: VALIDATE COINGECKO ID BEFORE STORING IN HISTORY
            raw_coin_id = coin_data.get('coin') or coin_data.get('id') or coin_data.get('symbol', 'unknown')
            logging.info(f"🔍 NEXT DEBUG: Got raw coin_id='{raw_coin_id}' from cache data")

            # Try to validate this ID works with CoinGecko
            proper_coin_id = None
            
            try:
                # Test if this ID works with CoinGecko API
                test_id, test_coin = await get_coin_info_ultra_fast(raw_coin_id)
                if test_id and test_coin:
                    proper_coin_id = test_id
                    logging.info(f"✅ NEXT DEBUG: Validated CoinGecko ID '{proper_coin_id}'")
                else:
                    # Try with symbol if original ID fails
                    symbol = coin_data.get('symbol', '').lower()
                    if symbol and symbol != raw_coin_id:
                        logging.info(f"🔍 NEXT DEBUG: Original ID failed, trying symbol '{symbol}'")
                        test_id, test_coin = await get_coin_info_ultra_fast(symbol)
                        if test_id and test_coin:
                            proper_coin_id = test_id
                            logging.info(f"✅ NEXT DEBUG: Symbol lookup successful, using '{proper_coin_id}'")
                        else:
                            # Try name as last resort
                            name = coin_data.get('name', '').lower().replace(' ', '-')
                            if name and name != raw_coin_id and name != symbol:
                                logging.info(f"🔍 NEXT DEBUG: Symbol failed, trying name '{name}'")
                                test_id, test_coin = await get_coin_info_ultra_fast(name)
                                if test_id and test_coin:
                                    proper_coin_id = test_id
                                    logging.info(f"✅ NEXT DEBUG: Name lookup successful, using '{proper_coin_id}'")
            except Exception as validation_error:
                logging.warning(f"🔍 NEXT DEBUG: Validation error for '{raw_coin_id}': {validation_error}")
            
            # Use proper ID or fallback to original
            if proper_coin_id:
                new_coin_id = proper_coin_id
                logging.info(f"✅ NEXT DEBUG: Using validated CoinGecko ID '{new_coin_id}' instead of '{raw_coin_id}'")
            else:
                new_coin_id = raw_coin_id
                logging.warning(f"⚠️ NEXT DEBUG: Could not validate '{raw_coin_id}', storing anyway (may cause BACK issues)")
            
            # Validate the final coin ID before adding to history
            if not new_coin_id or new_coin_id == 'unknown' or new_coin_id == '':
                logging.error(f"🔍 NEXT DEBUG: Invalid final coin ID, using fallback")
                new_coin_id = coin_data.get('symbol', f"cache_{current_index}")

            # Add to user's history with the validated ID
            session = add_to_user_history(user_id, new_coin_id)
            
            # Also update the coin object to ensure consistency
            coin['id'] = new_coin_id

            logging.info(f"🎰 User {user_id}: History updated - Added {new_coin_id} via NEXT at position {session['index']}/{len(session['history'])}")
            debug_user_session(user_id, "after NEXT button")

            # Format treasure discovery message
            msg = format_treasure_discovery_message(
                coin, 
                coin_data['fomo_score'], 
                coin_data['signal_type'], 
                coin_data['volume_spike']
            )
            msg += f"\n\n💰 <i>{spend_message}</i>"
            
            # Build keyboard with user's balance info
            fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
            user_balance_info = {
                'fcb_balance': fcb_balance,
                'free_queries_used': free_queries_used,
                'new_user_bonus_used': new_user_bonus_used,
                'total_free_remaining': total_free_remaining,
                'has_received_bonus': has_received_bonus
            }
            
            keyboard = build_addictive_buttons(coin, user_balance_info)
            
            # Try to send with logo first
            logo_url = coin.get('logo')
            if logo_url:
                try:
                    api_session = await get_optimized_session()
                    async with api_session.get(logo_url) as response:
                        if response.status == 200:
                            image_bytes = BytesIO(await response.read())
                            try:
                                await query.message.delete()
                                await context.bot.send_photo(
                                    chat_id=query.message.chat_id,
                                    photo=image_bytes,
                                    caption=msg,
                                    parse_mode='HTML',
                                    reply_markup=keyboard
                                )
                                logging.info(f"NEXT message sent with photo for {coin_data['symbol']}")
                                return
                            except Exception as photo_error:
                                logging.warning(f"Photo send failed in NEXT: {photo_error}")
                except Exception as e:
                    logging.warning(f"Image fetch failed in NEXT: {e}")

            # Fallback to text message
            await safe_edit_message(query, text=msg, reply_markup=keyboard)
            
            logging.info(f"User {user_id} spun for {coin_data['symbol']} - {spend_message}")

        else:
            await safe_edit_message(query, text="❌ No opportunities found right now. Try again in a few minutes!")
            
    except Exception as e:
        logging.error(f"Error in instant spin: {e}")
        await safe_edit_message(query, text="❌ Error finding opportunities. Please try again.")

async def handle_back_navigation(query, context, user_id):
    """Handle the BACK button with FREE navigation - PROPERLY FIXED VERSION"""
    
    # 🔧 DEBUG: Log the back request
    logging.info(f"🔍 BACK DEBUG: User {user_id} clicked back")
    
    try:
        # FREE navigation feedback
        await safe_edit_message(query, text="⬅️ <b>Going back... (FREE navigation)</b>")
        
        # Get user session with better error handling
        session = get_user_session(user_id)
        debug_user_session(user_id, "back button clicked")
        
        if not session.get('history') or len(session['history']) == 0:
            logging.warning(f"🔍 BACK DEBUG: No coin history for user {user_id}")
            await safe_edit_message(query, text="❌ No previous coins in this session. Try searching for a coin first!")
            return
        
        # 🔧 FIXED: Robust index validation and correction
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
        
        # 🔧 CRITICAL FIX: PROPER BACK NAVIGATION LOGIC
        if current_index > 0:
            # Move back to previous coin (decrease index by 1)
            new_index = current_index - 1
            session['index'] = new_index
            target_coin_id = session['history'][new_index]
            logging.info(f"⬅️ User {user_id}: Moving back from position {current_index + 1} to {new_index + 1}/{history_length}: {target_coin_id}")
        else:
            # Already at first coin, can't go back further
            target_coin_id = session['history'][0]
            logging.info(f"⬅️ User {user_id}: Already at first coin (position 1/{history_length}), refreshing: {target_coin_id}")
            await safe_edit_message(query, text="⬅️ You're already at the first coin in this session!")
            return
        
        # 🔧 VALIDATE: Check the coin ID before fetching - USING VALIDATION FUNCTION
        if not validate_coingecko_id(target_coin_id):
            logging.error(f"🔍 BACK DEBUG: Invalid/problematic coin ID '{target_coin_id}' rejected by validation")
            await safe_edit_message(query, text="❌ Invalid coin in history. Please start a new search.")
            return
        
        logging.info(f"🔍 BACK DEBUG: Attempting to fetch data for coin: {target_coin_id}")
        
# 🔧 ROBUST FETCH: Get coin info with intelligent fallback handling
        coin_id = None
        coin = None
        original_target = target_coin_id
        
        # Try multiple fetch strategies for better success rate
        fetch_attempts = [
            target_coin_id,  # Original ID
            target_coin_id.lower(),  # Lowercase version
            target_coin_id.replace('-', ''),  # Remove dashes
            target_coin_id.split('-')[0] if '-' in target_coin_id else target_coin_id  # First part before dash
        ]
        
        for attempt_id in fetch_attempts:
            try:
                logging.info(f"🔍 BACK DEBUG: Trying to fetch with ID: '{attempt_id}'")
                coin_id, coin = await get_coin_info_ultra_fast(attempt_id)
                
                if coin and coin is not None:
                    logging.info(f"✅ BACK DEBUG: Success with ID '{attempt_id}' for original '{original_target}'")
                    # Update the target_coin_id to the working one for consistency
                    target_coin_id = attempt_id
                    break
                else:
                    logging.warning(f"🔍 BACK DEBUG: No data for ID '{attempt_id}'")
                    
            except Exception as fetch_error:
                logging.warning(f"🔍 BACK DEBUG: Fetch error for '{attempt_id}': {fetch_error}")
                continue
        
        # If all fetch attempts failed, try to skip to previous coins
        if not coin or coin is None:
            logging.error(f"🔍 BACK DEBUG: All fetch attempts failed for {original_target}")
            
            # Try to skip to the previous coin in history if current one is delisted
            skip_attempts = 0
            max_skip_attempts = 5  # Try up to 5 previous coins
            
            while (not coin or coin is None) and skip_attempts < max_skip_attempts and session['index'] > 0:
                skip_attempts += 1
                logging.info(f"🔍 BACK DEBUG: Skip attempt {skip_attempts} - Moving to previous coin")
                
                # Move back one more position
                session['index'] -= 1
                if session['index'] < 0:
                    session['index'] = 0
                    break
                    
                next_target = session['history'][session['index']]
                logging.info(f"🔍 BACK DEBUG: Trying to skip to: {next_target}")
                
                # Try fetching this previous coin with the same multi-strategy approach
                for attempt_id in [next_target, next_target.lower(), next_target.replace('-', ''), 
                                 next_target.split('-')[0] if '-' in next_target else next_target]:
                    try:
                        coin_id, coin = await get_coin_info_ultra_fast(attempt_id)
                        if coin and coin is not None:
                            logging.info(f"✅ BACK DEBUG: Found valid coin after skipping: {attempt_id}")
                            target_coin_id = attempt_id
                            break
                    except Exception as fetch_error:
                        logging.warning(f"🔍 BACK DEBUG: Skip fetch error for {attempt_id}: {fetch_error}")
                        continue
                
                # If we found a valid coin, break out of the skip loop
                if coin and coin is not None:
                    break
            
            # If we still don't have a valid coin after all attempts
            if not coin or coin is None:
                logging.error(f"🔍 BACK DEBUG: No valid coins found after {skip_attempts} skip attempts")
                
                # Check if we have any history left at all
                if session['index'] <= 0 and len(session['history']) > 0:
                    error_msg = "❌ Reached the beginning of your session history, but previous coins are no longer available. Please start a new search."
                else:
                    error_msg = "❌ Unable to load any previous coins from your history. They may have been delisted or are temporarily unavailable. Please start a new search."
                    
                await safe_edit_message(query, text=error_msg)
                return
        
        logging.info(f"🔍 BACK DEBUG: Successfully fetched coin data for {coin_id or target_coin_id}")
        
        # 🔧 ANALYSIS: Run analysis with error handling
        fomo_score = 50  # Default values
        signal_type = "Analysis Failed"
        volume_spike = 1.0
        trend_status = "Unknown"
        distribution_status = "Unknown"
        
        try:
            fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
            logging.info(f"🔍 BACK DEBUG: Analysis complete - FOMO score: {fomo_score}")
        except Exception as analysis_error:
            logging.error(f"🔍 BACK DEBUG: Analysis error: {analysis_error}")
            # Continue with basic data if analysis fails
            signal_type = "Analysis Unavailable"
            trend_status = "Unknown"
            distribution_status = "Unknown"
        
        # Format message with error handling
        try:
            msg = format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast=False)
            
            # Add navigation info - FIXED CALCULATION
            position = session['index'] + 1  # Convert 0-based index to 1-based position
            total = len(session['history'])
            can_go_back = session['index'] > 0
            can_go_forward = session['index'] < total - 1
            
            # Add helpful navigation status
            nav_status = "⬅️ <i>Free navigation"
            if can_go_back and can_go_forward:
                nav_status += f" | Position {position}/{total} | Can go back/forward"
            elif can_go_back:
                nav_status += f" | Position {position}/{total} | Can go back"
            elif can_go_forward:
                nav_status += f" | Position {position}/{total} | Can go forward"
            else:
                nav_status += f" | Position {position}/{total} | Only coin"
            nav_status += "</i>"
            
            msg += f"\n\n{nav_status}"
            
        except Exception as format_error:
            logging.error(f"🔍 BACK DEBUG: Message formatting error: {format_error}")
            # Fallback simple message
            coin_name = coin.get('name', 'Unknown') if coin else target_coin_id
            msg = f"<b>{coin_name}</b>\n\n❌ Error formatting full analysis. Please try again or start a new search."
        
        # Get user balance for buttons
        try:
            fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
            user_balance_info = {
                'fcb_balance': fcb_balance,
                'free_queries_used': free_queries_used,
                'new_user_bonus_used': new_user_bonus_used,
                'total_free_remaining': total_free_remaining,
                'has_received_bonus': has_received_bonus
            }
            
            keyboard = build_addictive_buttons(coin, user_balance_info)
        except Exception as balance_error:
            logging.error(f"🔍 BACK DEBUG: Balance/keyboard error: {balance_error}")
            # Fallback keyboard
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('🎰 NEXT', callback_data="next_coin")],
                [InlineKeyboardButton('⭐ TOP UP', callback_data='buy_starter')]
            ])
        
        # 🔧 DISPLAY: Handle logo updates properly
        photo_sent = False
        logo_url = coin.get('logo') if coin else None
        
        if logo_url:
            try:
                api_session = await get_optimized_session()
                async with api_session.get(logo_url, timeout=10) as response:
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        
                        # Delete old message and send new one with photo
                        try:
                            await query.message.delete()
                            await context.bot.send_photo(
                                chat_id=query.message.chat_id,
                                photo=image_bytes,
                                caption=msg,
                                parse_mode='HTML',
                                reply_markup=keyboard
                            )
                            photo_sent = True
                            logging.info(f"✅ BACK navigation with photo: {target_coin_id}")
                        except Exception as photo_error:
                            logging.warning(f"Photo send failed in BACK: {photo_error}")
            except Exception as e:
                logging.warning(f"Image fetch failed in BACK: {e}")

        # Fallback to text message if photo fails
        if not photo_sent:
            await safe_edit_message(query, text=msg, reply_markup=keyboard)
        
        # Final logging with corrected position calculation
        final_position = session.get('index', 0) + 1
        total = len(session.get('history', []))
        logging.info(f"✅ BACK navigation complete: {target_coin_id} (position {final_position}/{total})")
        debug_user_session(user_id, "after back navigation")
        
    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in back navigation: {e}", exc_info=True)
        try:
            await safe_edit_message(query, text="❌ Error navigating back. Please try again or start a new search by typing a coin name.")
        except Exception as fallback_error:
            logging.error(f"❌ Even fallback message failed: {fallback_error}")
            # Last resort - just answer the callback
            try:
                await query.answer("Error occurred, please try again")
            except Exception:
                pass

async def handle_next_navigation(query, context, user_id):
    """Handle the NEXT button with smart navigation - FREE forward through history, then new discoveries"""
    
    # 🔧 DEBUG: Log the next request
    logging.info(f"🔍 NEXT DEBUG: User {user_id} clicked next")
    
    try:
        # Get user session
        session = get_user_session(user_id)
        debug_user_session(user_id, "next button clicked")
        
        # Check if user has history and current position
        history = session.get('history', [])
        current_index = session.get('index', 0)
        
        # 🔧 KEY LOGIC: Check if user can move FORWARD through existing history
        if history and current_index < len(history) - 1:
            # Validate the target coin ID before proceeding
            target_coin_id = history[current_index + 1]
            if not validate_coingecko_id(target_coin_id):
                logging.warning(f"🔍 NEXT DEBUG: Invalid coin ID in forward history: {target_coin_id}, falling back to new coin discovery")
                # Fall through to new coin discovery instead of showing error
            else:
                # FREE forward navigation feedback
                await safe_edit_message(query, text="➡️ <b>Moving forward... (FREE navigation)</b>")
                
                # Move forward to next coin in history
                new_index = current_index + 1
                session['index'] = new_index
                
                logging.info(f"➡️ User {user_id}: Moving forward from position {current_index + 1} to {new_index + 1}/{len(history)}: {target_coin_id}")
                
                # Use the same logic as your BACK button for fetching/displaying
                success = await display_coin_from_history_forward(query, context, user_id, target_coin_id)
                
                if success:
                    logging.info(f"✅ NEXT forward navigation complete: {target_coin_id} (position {new_index + 1}/{len(history)})")
                    return
                else:
                    # If coin from history failed, fall through to find new coin
                    logging.warning(f"🔍 NEXT DEBUG: Forward navigation failed, falling back to new coin discovery")
        
        # 🔧 NEW COIN DISCOVERY: User is at end of history or no history - find new coin
        logging.info(f"🔍 NEXT DEBUG: At end of history or no history, finding new coin")
        
        # Check if they have scans available for NEW discoveries
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        has_scans = total_free_remaining > 0 or fcb_balance > 0
        
        if not has_scans:
            # Show upgrade message for new discoveries
            message = format_out_of_scans_message("new coin")
            keyboard = build_out_of_scans_keyboard()
            await safe_edit_message(query, text=message, reply_markup=keyboard)
            return
        
        # Proceed with new coin discovery - CALL YOUR EXISTING FUNCTION
        await safe_edit_message(query, text="🎰 <b>Finding new opportunity...</b>")
        
        await handle_instant_spin(query, context, user_id)
        
    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in next navigation: {e}", exc_info=True)
        try:
            await safe_edit_message(query, text="❌ Error finding next coin. Please try again.")
        except Exception as fallback_error:
            logging.error(f"❌ Even fallback message failed: {fallback_error}")
            try:
                await query.answer("Error occurred, please try again")
            except Exception:
                pass

async def display_coin_from_history_forward(query, context, user_id, target_coin_id):
    """Display a coin from history for forward navigation - reuses your BACK logic"""
    
    logging.info(f"🔍 FORWARD DEBUG: Attempting to fetch data for coin: {target_coin_id}")
    
    # 🔧 ROBUST FETCH: Get coin info with intelligent fallback handling (same as BACK)
    coin_id = None
    coin = None
    original_target = target_coin_id
    
    # Try multiple fetch strategies for better success rate
    fetch_attempts = [
        target_coin_id,  # Original ID
        target_coin_id.lower(),  # Lowercase version
        target_coin_id.replace('-', ''),  # Remove dashes
        target_coin_id.split('-')[0] if '-' in target_coin_id else target_coin_id  # First part before dash
    ]
    
    for attempt_id in fetch_attempts:
        try:
            logging.info(f"🔍 FORWARD DEBUG: Trying to fetch with ID: '{attempt_id}'")
            coin_id, coin = await get_coin_info_ultra_fast(attempt_id)
            
            if coin and coin is not None:
                logging.info(f"✅ FORWARD DEBUG: Success with ID '{attempt_id}' for original '{original_target}'")
                target_coin_id = attempt_id
                break
            else:
                logging.warning(f"🔍 FORWARD DEBUG: No data for ID '{attempt_id}'")
                
        except Exception as fetch_error:
            logging.warning(f"🔍 FORWARD DEBUG: Fetch error for '{attempt_id}': {fetch_error}")
            continue
    
    # If fetch failed
    if not coin or coin is None:
        logging.error(f"🔍 FORWARD DEBUG: All fetch attempts failed for {original_target}")
        await safe_edit_message(query, text="❌ Unable to load coin from history. It may have been delisted.")
        return False
    
    # 🔧 ANALYSIS: Run analysis with error handling
    fomo_score = 50  # Default values
    signal_type = "Analysis Failed"
    volume_spike = 1.0
    trend_status = "Unknown"
    distribution_status = "Unknown"
    
    try:
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
        logging.info(f"🔍 FORWARD DEBUG: Analysis complete - FOMO score: {fomo_score}")
    except Exception as analysis_error:
        logging.error(f"🔍 FORWARD DEBUG: Analysis error: {analysis_error}")
        signal_type = "Analysis Unavailable"
        trend_status = "Unknown"
        distribution_status = "Unknown"
    
    # Format message with navigation info
    try:
        msg = format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast=False)
        
        # Add navigation info
        session = get_user_session(user_id)
        position = session['index'] + 1
        total = len(session['history'])
        can_go_back = session['index'] > 0
        can_go_forward = session['index'] < total - 1
        
        # Add helpful navigation status for FORWARD
        nav_status = "➡️ <i>Free navigation"
        
        if can_go_back and can_go_forward:
            nav_status += f" | Position {position}/{total} | Can go back/forward"
        elif can_go_back:
            nav_status += f" | Position {position}/{total} | Can go back | Next will find new coin"
        elif can_go_forward:
            nav_status += f" | Position {position}/{total} | Can go forward"
        else:
            nav_status += f" | Position {position}/{total} | Next will find new coin"
        nav_status += "</i>"
        
        msg += f"\n\n{nav_status}"
        
    except Exception as format_error:
        logging.error(f"🔍 FORWARD DEBUG: Message formatting error: {format_error}")
        coin_name = coin.get('name', 'Unknown') if coin else target_coin_id
        msg = f"<b>{coin_name}</b>\n\n❌ Error formatting analysis. Please try again."
    
    # Get keyboard
    try:
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        user_balance_info = {
            'fcb_balance': fcb_balance,
            'free_queries_used': free_queries_used,
            'new_user_bonus_used': new_user_bonus_used,
            'total_free_remaining': total_free_remaining,
            'has_received_bonus': has_received_bonus
        }
        keyboard = build_addictive_buttons(coin, user_balance_info)
    except Exception as balance_error:
        logging.error(f"🔍 FORWARD DEBUG: Balance/keyboard error: {balance_error}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('🎰 NEXT', callback_data="next_coin")],
            [InlineKeyboardButton('⭐ TOP UP', callback_data='buy_starter')]
        ])
    
    # Display with photo if available
    photo_sent = False
    logo_url = coin.get('logo') if coin else None
    
    if logo_url:
        try:
            api_session = await get_optimized_session()
            async with api_session.get(logo_url, timeout=10) as response:
                if response.status == 200:
                    image_bytes = BytesIO(await response.read())
                    
                    try:
                        await query.message.delete()
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=image_bytes,
                            caption=msg,
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                        photo_sent = True
                        logging.info(f"✅ Forward navigation with photo: {target_coin_id}")
                    except Exception as photo_error:
                        logging.warning(f"Photo send failed in forward: {photo_error}")
        except Exception as e:
            logging.warning(f"Image fetch failed in forward: {e}")

    # Fallback to text message if photo fails
    if not photo_sent:
        await safe_edit_message(query, text=msg, reply_markup=keyboard)
    
    return True

async def send_coin_message_ultra_fast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ULTRA-FAST coin message handler - FIXED HISTORY TRACKING"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    logging.info(f"🔍 DEBUG: User {user_id} requested: '{query}'")
    
    # Rate limit check
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
    logging.info(f"🔍 DEBUG: Rate limit check - allowed: {allowed}, reason: '{reason}', time_remaining: {time_remaining}")

    if not allowed:
        if reason == "No queries available":
            logging.info(f"🔍 DEBUG: User {user_id} out of scans - sending out of scans message")
            try:
                message = format_out_of_scans_message_with_back(query)
                keyboard = build_out_of_scans_keyboard_with_back(query)
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
                logging.info(f"✅ DEBUG: Enhanced out of scans message sent to user {user_id}")
                return
            except Exception as e:
                logging.error(f"❌ DEBUG: Failed to send enhanced message: {e}")
                # Emergency fallback message
                try:
                    fallback_message = f"""💔 <b>Out of FOMO Scans!</b>

You've used all your free scans for today.

🎯 <b>Get More Scans:</b>
- Buy FCB tokens with /buy
- Get unlimited scans instantly!

Type /buy to get started! 🚀"""
                    
                    fallback_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⭐ Buy Tokens", callback_data="buy_starter")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]
                    ])
                    
                    await update.message.reply_text(fallback_message, parse_mode='HTML', reply_markup=fallback_keyboard)
                    logging.info(f"✅ DEBUG: Fallback message sent to user {user_id}")
                except Exception as fallback_error:
                    logging.error(f"❌ DEBUG: Even fallback message failed: {fallback_error}")
        else:
            logging.info(f"🔍 DEBUG: User {user_id} rate limited - sending countdown message")
            try:
                countdown_msg = create_countdown_visual(time_remaining)
                countdown_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]
                ])
                await update.message.reply_text(countdown_msg, parse_mode='HTML', reply_markup=countdown_keyboard)
                logging.info(f"✅ DEBUG: Countdown message sent to user {user_id}")
            except Exception as e:
                logging.error(f"❌ DEBUG: Failed to send countdown message: {e}")
        return
    
    # Continue with normal processing if user has scans available
    logging.info(f"🔍 DEBUG: User {user_id} has scans available, proceeding with analysis")
    
    # Spend the query
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        await update.message.reply_text(spend_message, parse_mode='HTML')
        return
    
    # ULTRA-FAST progressive loading
    searching_msg = await update.message.reply_text('🔍 <b>Analyzing...</b>', parse_mode='HTML')
    
    try:
        # Get coin info with ultra-fast lookup
        coin_id, coin = await get_coin_info_ultra_fast(query)
        
        # 🔧 ADD: Debug the coin lookup result
        logging.info(f"🔍 COIN LOOKUP DEBUG: query='{query}' -> coin_id='{coin_id}', has_coin_data={bool(coin)}")

        if not coin:
            await searching_msg.edit_text('❌ Coin not found! Please check spelling.')
            return

        # 🔧 FIXED: USER-SPECIFIC HISTORY TRACKING
        session = add_to_user_history(user_id, coin_id)
        debug_user_session(user_id, "after coin search")
        
        # Show basic info immediately
        from formatters import short_stat, emoji_for_percent
        
        name = f"{coin.get('name', 'Unknown')} ({coin.get('symbol', '')})"
        price = short_stat(coin.get("price"))
        p1 = coin.get("change_1h", 0) or 0
        p24 = coin.get("change_24h", 0) or 0
        
        quick_msg = f"""⚡ <b>Quick Analysis</b>

<b>{name}</b>
💰 <b>Price:</b> {price}
📊 1hr: {emoji_for_percent(p1)} <b>{p1:+.1f}%</b> | 24hr: {emoji_for_percent(p24)} <b>{p24:+.1f}%</b>

🚀 <i>Running ULTRA-FAST analysis...</i>"""
        
        await searching_msg.edit_text(quick_msg, parse_mode='HTML')
        
        # Run ULTRA-FAST parallel analysis
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
        
        # Format complete message
        msg = format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast=False)
        msg += f"\n\n💰 <i>{spend_message}</i>"
        
        # Build keyboard with user's balance info
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        user_balance_info = {
            'fcb_balance': fcb_balance,
            'free_queries_used': free_queries_used,
            'new_user_bonus_used': new_user_bonus_used,
            'total_free_remaining': total_free_remaining,
            'has_received_bonus': has_received_bonus
        }
        
        keyboard = build_addictive_buttons(coin, user_balance_info)
        
        # Clean up and send final message
        try:
            await searching_msg.delete()
        except:
            pass
        
        # Try with logo
        logo_url = coin.get('logo')
        if logo_url:
            try:
                api_session = await get_optimized_session()    # ← FIXED
                async with api_session.get(logo_url) as response:    # ← FIXED
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        await update.message.reply_photo(photo=image_bytes, caption=msg, parse_mode='HTML', reply_markup=keyboard)
                        return
            except:
                pass
                
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
        
        logging.info(f"✅ ULTRA-FAST analysis complete for {query} - User session properly updated!")
        
    except Exception as e:
        logging.error(f"Error in ultra-fast analysis: {e}")
        try:
            await searching_msg.edit_text('❌ Error processing request. Please try again.')
        except:
            await update.message.reply_text('❌ Error processing request. Please try again.')

# =============================================================================
# ENHANCED NAVIGATION HANDLERS
# =============================================================================

async def handle_back_to_main(query, context, user_id):
    """Handle back to main menu action"""
    
    # Get user's current balance for a helpful main menu
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    # Check if user has any coin history for the BACK button (they always should if they're here)
    session = get_user_session(user_id)
    # Note: Users only reach this main menu after using scans, so they should always have history
    
    main_menu_msg = f"""👋 Welcome back to FOMO Crypto Bot!

📊 Your Status:
🎯 FOMO Scans: {total_free_remaining} remaining
💎 FCB Tokens: {fcb_balance}

✨ What would you like to do?

💡 Quick Actions:
- Type any coin name (like "bitcoin", "pepe") to analyze
- Use /balance to check your scans
- Use /buy to get more FCB tokens

📺 Follow our alerts: https://t.me/fomocryptobot_alert

Ready to find the next moon shot? 🚀"""

    # Create simple keyboard - always show BACK since users only reach main menu after using scans
    keyboard_buttons = []
    
    # First row - navigation buttons
    keyboard_buttons.append([
        InlineKeyboardButton("⬅️ BACK", callback_data="back_navigation"),
        InlineKeyboardButton("📊 My Balance", callback_data="check_balance")
    ])
    
    # Second row - purchase and help
    keyboard_buttons.append([
        InlineKeyboardButton("⭐ Buy Tokens", callback_data="buy_starter"),
        InlineKeyboardButton("❓ Help", callback_data="show_help")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await safe_edit_message(query, text=main_menu_msg, reply_markup=keyboard)

async def handle_rate_limit_info(query, context, user_id):
    """Show rate limit information and alternatives"""
    
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    info_msg = f"""⏰ Rate Limit Information

📊 Your Current Status:
🎯 FOMO Scans: {total_free_remaining} remaining
💎 FCB Tokens: {fcb_balance}

🕒 How it works:
- Free users: 1 second between queries
- This protects our API costs
- Premium users: No rate limits

⏰ When do scans reset?
- Daily scans: Reset at midnight UTC
- New user bonus: One-time only
- FCB tokens: Never expire

💡 Alternatives while you wait:
- Check our channel for latest alerts
- Plan your next analysis
- Consider upgrading for instant access"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 View Channel", url="https://t.me/fomocryptobot_alert")],
        [
            InlineKeyboardButton("⭐ Go Premium", callback_data="buy_starter"),
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")
        ]
    ])
    
    await safe_edit_message(query, text=info_msg, reply_markup=keyboard)

async def handle_show_help(query, context, user_id):
    """Show help information"""
    
    help_msg = get_help_message()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]
    ])
    
    await safe_edit_message(query, text=help_msg, reply_markup=keyboard)

# =============================================================================
# CALLBACK HANDLERS
# =============================================================================

async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced callback handler with back button support"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Handle new back navigation options
    if query.data == "back_to_main":
        await handle_back_to_main(query, context, user_id)
        return
    
    elif query.data == "show_rate_limit_info":
        await handle_rate_limit_info(query, context, user_id)
        return
    
    elif query.data == "show_help":
        await handle_show_help(query, context, user_id)
        return
    
    # Handle purchase buttons FIRST (no rate limiting needed)
    elif query.data.startswith("buy_"):
        await handle_star_purchase(update, context)
        return
    
    # Handle Back button with instant response  
    elif query.data.startswith("back_"):
        await handle_back_navigation(query, context, user_id)
        return
    
    elif query.data == "check_balance":
        user_id = query.from_user.id
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        message = f"""📊 <b>Balance Update</b>
        
🎯 FOMO Scans: <b>{total_free_remaining} remaining</b>
💎 FCB Tokens: <b>{fcb_balance}</b>

💡 <b>Need more scans?</b>
- Daily scans reset at midnight
- Buy FCB tokens for unlimited access
- Premium users never run out!"""
        
        # Add helpful keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Buy More Scans", callback_data="buy_starter")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
        ])
        
        await safe_edit_message(query, text=message, reply_markup=keyboard)
        return
    
    # Check if user has queries available
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
    
    if not allowed:
        if reason == "No queries available":
            message = format_out_of_scans_back_message_with_navigation()
            keyboard = build_out_of_scans_back_keyboard_with_navigation()
            await safe_edit_message(query, text=message, reply_markup=keyboard)
        else:
            countdown_msg = create_countdown_visual(time_remaining)
            # Add back button to countdown too
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main")]
            ])
            await safe_edit_message(query, text=countdown_msg, reply_markup=keyboard)
        return
    
    # Handle Next/Spin button with instant response
    elif query.data == "next_coin":
        await handle_next_navigation(query, context, user_id)
    
    else:
        logging.warning(f"UNKNOWN CALLBACK: '{query.data}'")
        await safe_edit_message(query, text="❌ Unknown action. Please try again.")

# =============================================================================
# PAYMENT HANDLERS
# =============================================================================

async def handle_star_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle star purchase button clicks"""
    query = update.callback_query
    
    package_key = query.data.replace("buy_", "")
    if package_key in FCB_STAR_PACKAGES:
        package = FCB_STAR_PACKAGES[package_key]
        
        try:
            # Send Stars invoice (provider_token is empty for Stars)
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=package['title'],
                description=package['description'],
                payload=f"fcb_{package_key}_{query.from_user.id}",
                provider_token="",  # Empty for Telegram Stars!
                currency="XTR",     # XTR = Telegram Stars
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
    """Handle pre-checkout validation"""
    query = update.pre_checkout_query
    
    # Validate FCB token purchases
    if query.invoice_payload.startswith("fcb_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid purchase")

async def payment_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful Stars payments - FIXED VERSION"""
    payment = update.message.successful_payment
    actual_buyer_id = update.effective_user.id  # Get the actual buyer's ID
    
    # Add debug logging
    logging.info(f"🔍 PAYMENT DEBUG: Buyer ID: {actual_buyer_id}")
    logging.info(f"🔍 PAYMENT DEBUG: Payload: {payment.invoice_payload}")
    logging.info(f"🔍 PAYMENT DEBUG: Stars amount: {payment.total_amount}")
    
    # Parse payload
    payload_parts = payment.invoice_payload.split("_")
    
    if len(payload_parts) == 3 and payload_parts[0] == "fcb":
        package_key = payload_parts[1]
        payload_user_id = int(payload_parts[2])
        
        # Security check: ensure the buyer matches the payload
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
            
            # Add tokens with verification
            success, new_balance = add_fcb_tokens(actual_buyer_id, tokens)
            
            if success:
                # Record first purchase date
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
                
                # Send success message with balance confirmation
                message = f"""🎉 <b>Purchase Successful!</b>

💎 <b>{tokens} FCB tokens</b> added to your account!
⭐ <b>{stars} Stars</b> spent

📊 <b>Your Balance:</b>
💎 FCB Tokens: <b>{new_balance}</b>
🎯 FOMO Scans: <b>Unlimited with tokens!</b>

🚀 <b>Ready to scan?</b> Type any coin name to get started!"""
                
                await update.message.reply_text(message, parse_mode='HTML')
                
                logging.info(f"✅ PAYMENT SUCCESS: User {actual_buyer_id} bought {tokens} FCB tokens for {stars} Stars - New balance: {new_balance}")
            else:
                # Handle database failure
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
# ERROR HANDLER
# =============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    logging.error(msg='Exception while handling an update:', exc_info=context.error)
    
    # Try to send a user-friendly error message if possible
    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again in a moment.",
                parse_mode='HTML'
            )
        except TelegramError:
            # If we can't send a message, just log it
            logging.error("Could not send error message to user")

# =============================================================================
# HANDLER SETUP FUNCTION
# =============================================================================

def setup_handlers(app):
    """Setup all handlers for the bot application"""
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
    
    # Initialize database
    from database import init_user_db
    init_user_db()
    
    # Command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('terms', terms_command))
    app.add_handler(CommandHandler('buy', buy_command))
    app.add_handler(CommandHandler('debug', debug_balance_command))
    app.add_handler(CommandHandler('balance', balance_command))
    app.add_handler(CommandHandler('test', test_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('unsubscribe', unsubscribe_command))
    app.add_handler(CommandHandler('debugsession', debug_session_command))  # NEW - session debug
    
    # Callback query handler for ALL buttons (purchase + addictive buttons)
    app.add_handler(CallbackQueryHandler(handle_callback_queries))
    
    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success_handler))
    
    # Main message handler for coin analysis (ULTRA-FAST)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_coin_message_ultra_fast))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logging.info("✅ All handlers setup complete with session-based navigation!")