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
    build_addictive_buttons, build_purchase_keyboard, build_out_of_scans_keyboard,
    build_out_of_scans_back_keyboard, create_countdown_visual,
    get_start_message, get_help_message
)
from cache import get_ultra_fast_fomo_opportunities
from scanner import add_user_to_notifications, subscribed_users, save_subscriptions

user_sessions = {}  # {user_id: {'history': [], 'index': 0, 'last_activity': timestamp}}

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
    """Handle the 'NEXT' button with instant treasure discovery - FIXED HISTORY TRACKING"""
    
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
            
            # 🔧 FIXED: UPDATE USER-SPECIFIC HISTORY WHEN SPINNING TO NEW COIN
            new_coin_id = coin_data.get('coin') or coin_data.get('id') or coin_data.get('symbol', 'unknown')
            logging.info(f"🔍 NEXT DEBUG: Got coin_id='{new_coin_id}' from cache data: {coin_data}")

            # Validate the coin ID before adding to history
            if not new_coin_id or new_coin_id == 'unknown' or new_coin_id == '':
                logging.error(f"🔍 NEXT DEBUG: Invalid coin ID from cache: {coin_data}")
                new_coin_id = coin_data.get('symbol', f"cache_{current_index}")

            # Add to user's history
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
                    api_session = await get_optimized_session()    # ← CHANGED
                    async with api_session.get(logo_url) as response:    # ← CHANGED
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
    """Handle the BACK button with FREE navigation - FIXED USER SESSIONS"""
    
    # 🔧 DEBUG: Log the back request
    logging.info(f"🔍 BACK DEBUG: User {user_id} clicked back")
    debug_user_session(user_id, "back button clicked")
    
    # Check if they have ANY scans available (just to prevent complete freeloaders)
    fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
    has_any_scans = total_free_remaining > 0 or fcb_balance > 0
    
    if not has_any_scans:
        # Only show upgrade if they have zero scans
        message = format_out_of_scans_back_message()
        keyboard = build_out_of_scans_back_keyboard()
        await safe_edit_message(query, text=message, reply_markup=keyboard)
        return
    
    # FREE navigation
    await safe_edit_message(query, text="⬅️ <b>Going back... (FREE navigation)</b>")
    
    try:
        # Get user session
        session = get_user_session(user_id)
        
        if not session['history']:
            logging.warning(f"🔍 BACK DEBUG: No coin history for user {user_id}")
            await safe_edit_message(query, text="❌ No previous coins in this session.")
            return
        
        # 🔧 FIXED: Validate current index
        if session['index'] < 0 or session['index'] >= len(session['history']):
            logging.error(f"🔍 BACK DEBUG: Invalid index {session['index']} for history length {len(session['history'])}")
            # Reset to last valid position
            session['index'] = len(session['history']) - 1
            logging.info(f"🔍 BACK DEBUG: Reset index to {session['index']}")
        
        # 🔧 PROPER BACK NAVIGATION LOGIC
        if session['index'] > 0:
            # Move back to previous coin
            session['index'] -= 1
            previous_coin_id = session['history'][session['index']]
            logging.info(f"⬅️ User {user_id}: Moving back to position {session['index'] + 1}/{len(session['history'])}: {previous_coin_id}")
        else:
            # Already at first coin, stay there
            previous_coin_id = session['history'][0]
            logging.info(f"⬅️ User {user_id}: Already at first coin: {previous_coin_id}")
        
        # 🔧 VALIDATE: Check the coin ID before fetching
        if not previous_coin_id or previous_coin_id == 'unknown' or previous_coin_id == '':
            logging.error(f"🔍 BACK DEBUG: Invalid coin ID '{previous_coin_id}' at position {session['index']}")
            await safe_edit_message(query, text="❌ Invalid coin in history. Please start a new search.")
            return
        
        logging.info(f"🔍 BACK DEBUG: Attempting to fetch data for coin: {previous_coin_id}")
        
        # 🔧 FETCH: Get coin info with better error handling
        try:
            coin_id, coin = await get_coin_info_ultra_fast(previous_coin_id)
            logging.info(f"🔍 BACK DEBUG: Fetch result - coin_id: {coin_id}, coin data exists: {bool(coin)}")
        except Exception as fetch_error:
            logging.error(f"🔍 BACK DEBUG: Fetch error for {previous_coin_id}: {fetch_error}")
            await safe_edit_message(query, text=f"❌ Error fetching data for {previous_coin_id}. It may have been delisted.")
            return
        
        if not coin:
            logging.error(f"🔍 BACK DEBUG: No coin data returned for {previous_coin_id}")
            
            # Try to skip to the previous coin in history if current one is delisted
            attempts = 0
            max_attempts = 3  # Prevent infinite loops
            
            while not coin and attempts < max_attempts and session['index'] > 0:
                attempts += 1
                logging.info(f"🔍 BACK DEBUG: Attempt {attempts} - Trying to skip delisted coin {previous_coin_id}")
                
                # Move back one more position
                session['index'] -= 1
                previous_coin_id = session['history'][session['index']]
                
                # Try fetching this previous coin
                try:
                    coin_id, coin = await get_coin_info_ultra_fast(previous_coin_id)
                    if coin:
                        logging.info(f"✅ BACK DEBUG: Found valid coin after skipping: {previous_coin_id}")
                        break
                    else:
                        logging.warning(f"🔍 BACK DEBUG: Coin {previous_coin_id} also delisted, trying next...")
                except Exception as fetch_error:
                    logging.error(f"🔍 BACK DEBUG: Error fetching {previous_coin_id}: {fetch_error}")
            
            # If we still don't have a valid coin after attempts
            if not coin:
                if session['index'] <= 0:
                    await safe_edit_message(query, text="❌ All previous coins in history appear to be delisted. Please start a new search.")
                else:
                    await safe_edit_message(query, text="❌ Unable to find any valid previous coins. Please start a new search.")
                return
        
        logging.info(f"🔍 BACK DEBUG: Successfully fetched coin data for {coin_id}")
        
        # 🔧 ANALYSIS: Run analysis with error handling
        try:
            fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
            logging.info(f"🔍 BACK DEBUG: Analysis complete - FOMO score: {fomo_score}")
        except Exception as analysis_error:
            logging.error(f"🔍 BACK DEBUG: Analysis error: {analysis_error}")
            # Continue with basic data if analysis fails
            fomo_score, signal_type, volume_spike = 50, "Analysis Failed", 1.0
            trend_status, distribution_status = "Unknown", "Unknown"
        
        # Format message
        msg = format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast=False)
        
        # Add navigation info
        position = session['index'] + 1
        total = len(session['history'])
        msg += f"\n\n⬅️ <i>History: {position}/{total} | Free navigation</i>"
        
        # Get user balance for buttons
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        user_balance_info = {
            'fcb_balance': fcb_balance,
            'free_queries_used': free_queries_used,
            'new_user_bonus_used': new_user_bonus_used,
            'total_free_remaining': total_free_remaining,
            'has_received_bonus': has_received_bonus
        }
        
        keyboard = build_addictive_buttons(coin, user_balance_info)
        
        # 🔧 DISPLAY: Handle logo updates properly
        logo_url = coin.get('logo')
        if logo_url:
            try:
                api_session = await get_optimized_session()  # RENAMED to avoid conflict
                async with api_session.get(logo_url) as response:
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
                            logging.info(f"✅ BACK navigation with photo: {previous_coin_id} (position {position}/{total})")
                            return
                        except Exception as photo_error:
                            logging.warning(f"Photo send failed in BACK: {photo_error}")
            except Exception as e:
                logging.warning(f"Image fetch failed in BACK: {e}")

        # Fallback to text message if photo fails
        await safe_edit_message(query, text=msg, reply_markup=keyboard)
        
        logging.info(f"✅ BACK navigation complete: {previous_coin_id} (position {position}/{total})")
        debug_user_session(user_id, "after back navigation")
        
    except Exception as e:
        logging.error(f"❌ Error in back navigation: {e}", exc_info=True)
        await safe_edit_message(query, text="❌ Error navigating back. Please try again or start a new search.")

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
            logging.info(f"🔍 DEBUG: User {user_id} out of scans - attempting to send out of scans message")
            try:
                message = format_out_of_scans_message(query)
                keyboard = build_out_of_scans_keyboard(query)
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
                logging.info(f"✅ DEBUG: Out of scans message sent successfully to user {user_id}")
                return
            except Exception as e:
                logging.error(f"❌ DEBUG: Failed to send out of scans message to user {user_id}: {e}")
                # Emergency fallback message
                try:
                    fallback_message = f"""💔 <b>Out of FOMO Scans!</b>

You've used all your free scans for today.

🎯 <b>Get More Scans:</b>
- Buy FCB tokens with /buy
- Get unlimited scans instantly!

💡 <b>Why FCB tokens?</b>
- No daily limits
- Instant FOMO analysis
- Premium features

Type /buy to get started! 🚀"""
                    
                    await update.message.reply_text(fallback_message, parse_mode='HTML')
                    logging.info(f"✅ DEBUG: Fallback message sent to user {user_id}")
                except Exception as fallback_error:
                    logging.error(f"❌ DEBUG: Even fallback message failed: {fallback_error}")
        else:
            logging.info(f"🔍 DEBUG: User {user_id} rate limited - sending countdown message")
            try:
                countdown_msg = create_countdown_visual(time_remaining)
                await update.message.reply_text(countdown_msg, parse_mode='HTML')
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
# CALLBACK HANDLERS
# =============================================================================

async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries (buttons) with instant gratification"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Handle purchase buttons FIRST (no rate limiting needed)
    if query.data.startswith("buy_"):
        await handle_star_purchase(update, context)
        return
    
    # Handle Back button with instant response  
    if query.data.startswith("back_"):
        await handle_back_navigation(query, context, user_id)
        return
    
    elif query.data == "check_balance":
        user_id = query.from_user.id
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        message = f"""📊 <b>Balance Update</b>
        
🎯 FOMO Scans: <b>{total_free_remaining} remaining</b>
💎 FCB Tokens: <b>{fcb_balance}</b>"""
        
        await safe_edit_message(query, text=message)
        return
    
    # Check if user has queries available
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
    
    if not allowed:
        if reason == "No queries available":
            message = format_out_of_scans_back_message()
            keyboard = build_out_of_scans_back_keyboard()
            await safe_edit_message(query, text=message, reply_markup=keyboard)
        else:
            countdown_msg = create_countdown_visual(time_remaining)
            await safe_edit_message(query, text=countdown_msg)
        return
    
    # Handle Next/Spin button with instant response
    elif query.data == "next_coin":
        await handle_instant_spin(query, context, user_id)
    
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