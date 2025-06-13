"""
Telegram handlers module for CFB (Crypto FOMO Bot)
Handles all Telegram bot interactions, commands, and callbacks
"""

import logging
import random
import asyncio
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
    format_out_of_scans_refresh_message, format_payment_success_message,
    build_addictive_buttons, build_purchase_keyboard, build_out_of_scans_keyboard,
    build_out_of_scans_refresh_keyboard, create_countdown_visual,
    get_start_message, get_help_message
)
from cache import get_ultra_fast_fomo_opportunities
from scanner import add_user_to_notifications, subscribed_users

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

✅ **You're now subscribed to FOMO alerts!**

You'll receive high-quality FOMO alerts directly here with full interactivity:
- 🔄 REFRESH button works
- 🎰 NEXT button works  
- 💰 BUY button works

📺 See our public track record: https://t.me/fomocryptobot_alert

💡 **New Commands:**
- `/test` - Test your notification subscription
- `/status` - Check subscriber count and your status

Type any coin name to test the bot!"""
    
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

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  # ✅ CORRECT INDENTATION!
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
        await update.message.reply_text("🛑 You’ve been unsubscribed from FOMO alerts.", parse_mode='HTML')
        logging.info(f"User {username} (ID: {user_id}) unsubscribed from FOMO alerts")
    else:
        await update.message.reply_text("ℹ️ You are not currently subscribed.", parse_mode='HTML')

# =============================================================================
# ULTRA-FAST MESSAGE HANDLERS
# =============================================================================

async def handle_instant_update(query, context, coin_id, user_id):
    """Super fast update with progressive loading - NOW 5x FASTER!"""
    
    # Spend the query first
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        try:
            await query.edit_message_text(spend_message, parse_mode='HTML')
        except Exception:
            # If can't edit, send new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=spend_message,
                parse_mode='HTML'
            )
        return
    
    # INSTANT visual feedback with better error handling
    instant_msg = random.choice(INSTANT_SPIN_RESPONSES)
    try:
        # Try to edit the message text first
        await query.edit_message_text(f"🎰 <b>{instant_msg}</b>", parse_mode='HTML')
    except Exception as e:
        error_msg = str(e).lower()
        if "no text in the message to edit" in error_msg:
            # Message is probably a photo - try editing caption instead
            try:
                await query.edit_message_caption(caption=f"🎰 <b>{instant_msg}</b>", parse_mode='HTML')
            except Exception:
                # If that fails too, delete and send new message
                try:
                    await query.message.delete()
                except Exception:
                    pass  # Message might already be deleted
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"🎰 <b>{instant_msg}</b>",
                    parse_mode='HTML'
                )
        else:
            # For other errors, just answer the callback
            await query.answer("Processing...")
    
    try:
        # Get coin info with ultra-fast lookup
        coin_id, coin = await get_coin_info_ultra_fast(coin_id)
        
        if not coin:
            error_message = "❌ Unable to fetch updated data. Coin may have been delisted."
            try:
                await query.edit_message_text(error_message, parse_mode='HTML')
            except Exception:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=error_message,
                    parse_mode='HTML'
                )
            return
        
        # Show basic info immediately
        from formatters import short_stat, emoji_for_percent, get_simple_timestamp
        
        name = f"{coin.get('name', 'Unknown')} ({coin.get('symbol', '')})"
        price = short_stat(coin.get("price"))
        p1 = coin.get("change_1h", 0) or 0
        p24 = coin.get("change_24h", 0) or 0
        v24 = int(coin.get("volume", 0) or 0)
        
        quick_msg = f"""🔄 <b>Refreshing Analysis</b>

<b>{name}</b>
💰 <b>Price:</b> {price}
📊 1hr: {emoji_for_percent(p1)} <b>{p1:+.1f}%</b> | 24hr: {emoji_for_percent(p24)} <b>{p24:+.1f}%</b>
📈 <b>Volume:</b> ${v24:,}

⚡ <i>Running ULTRA-FAST analysis...</i>"""
        
        try:
            await query.edit_message_text(quick_msg, parse_mode='HTML')
        except Exception:
            # If edit fails, send new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=quick_msg,
                parse_mode='HTML'
            )
        
        # Run ULTRA-FAST parallel analysis
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin)
        
        # Complete message
        msg = format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast=False)
        msg += f"\n\n🔄 <i>Updated: {get_simple_timestamp()}</i>"
        msg += f"\n💰 <i>{spend_message}</i>"
        
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
        
        try:
            await query.edit_message_text(msg, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
        except Exception:
            # If edit fails, send new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=msg,
                parse_mode='HTML',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        
        logging.info(f"✅ ULTRA-FAST refresh complete for {coin_id}")
        
    except Exception as e:
        logging.error(f"Error updating coin {coin_id}: {e}")
        error_message = "❌ Error updating data. Please try again."
        try:
            await query.edit_message_text(error_message, parse_mode='HTML')
        except Exception:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=error_message,
                parse_mode='HTML'
            )

async def handle_instant_spin(query, context, user_id):
    """Handle the 'NEXT' button with instant treasure discovery"""
    
    # Spend the query first
    success, spend_message = spend_fcb_token(user_id)
    if not success:
        try:
            await query.edit_message_text(spend_message, parse_mode='HTML')
        except:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=spend_message,
                parse_mode='HTML'
            )
        return
    
    # INSTANT visual feedback
    instant_msg = random.choice(INSTANT_SPIN_RESPONSES)
    try:
        await query.edit_message_text(f"🎰 <b>{instant_msg}</b>", parse_mode='HTML')
    except Exception as e:
        if "no text in the message to edit" in str(e).lower():
            # If the original message has no text, send a new message instead
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"🎰 <b>{instant_msg}</b>",
                parse_mode='HTML'
            )
        else:
            # For other errors, still try to answer the callback
            await query.answer("Processing...")
    
    try:
        # Check if we have cached opportunities
        global FOMO_CACHE
        if not FOMO_CACHE['coins'] or not FOMO_CACHE['coins']:
            # Fallback to live search if cache is empty
            try:
                await query.edit_message_text("🔍 <b>Searching for fresh opportunities...</b>", parse_mode='HTML')
            except:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="🔍 <b>Searching for fresh opportunities...</b>",
                    parse_mode='HTML'
                )
            
            # Quick scan for opportunities
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
            
            # DEBUG: Check what data we have
            logging.info(f"DEBUG - coin_data keys: {list(coin_data.keys())}")
            logging.info(f"DEBUG - coin object: {coin}")
            
            # Format treasure discovery message
            msg = format_treasure_discovery_message(
                coin, 
                coin_data['fomo_score'], 
                coin_data['signal_type'], 
                coin_data['volume_spike']
            )
            msg += f"\n\n💰 <i>{spend_message}</i>"
            
            keyboard = build_addictive_buttons(coin)
            
# Try to send with logo first
            logo_url = coin.get('logo')
            if logo_url:
                try:
                    session = await get_optimized_session()
                    async with session.get(logo_url) as response:
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
            try:
                await query.edit_message_text(
                    msg, 
                    parse_mode='HTML', 
                    reply_markup=keyboard, 
                    disable_web_page_preview=True
                )
            except:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=msg,
                    parse_mode='HTML',
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            
            logging.info(f"User {user_id} spun for {coin_data['symbol']} - {spend_message}")

        else:
            try:
                await query.edit_message_text(
                    "❌ No opportunities found right now. Try again in a few minutes!",
                    parse_mode='HTML'
                )
            except:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ No opportunities found right now. Try again in a few minutes!",
                    parse_mode='HTML'
                )
            
    except Exception as e:
        logging.error(f"Error in instant spin: {e}")
        try:
            await query.edit_message_text("❌ Error finding opportunities. Please try again.", parse_mode='HTML')
        except:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Error finding opportunities. Please try again.",
                parse_mode='HTML'
            )

async def send_coin_message_ultra_fast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ULTRA-FAST coin message handler - NOW 5x FASTER!"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    logging.info(f"User {user_id} requested: {query}")
    
    # Check rate limit (now only 1 second!)
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
    
    if not allowed:
        if reason == "No queries available":
            message = format_out_of_scans_message(query)
            keyboard = build_out_of_scans_keyboard(query)
            await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
        else:
            countdown_msg = create_countdown_visual(time_remaining)
            await update.message.reply_text(countdown_msg, parse_mode='HTML')
        return
    
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
        
        if not coin:
            await searching_msg.edit_text('❌ Coin not found! Please check spelling.')
            return
        
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
        
        keyboard = build_addictive_buttons(coin)
        
        # Clean up and send final message
        try:
            await searching_msg.delete()
        except:
            pass
        
        # Try with logo
        logo_url = coin.get('logo')
        if logo_url:
            try:
                session = await get_optimized_session()
                async with session.get(logo_url) as response:
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        await update.message.reply_photo(photo=image_bytes, caption=msg, parse_mode='HTML', reply_markup=keyboard)
                        return
            except:
                pass
                
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
        
        logging.info(f"✅ ULTRA-FAST analysis complete for {query} - 5x faster than before!")
        
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
    
    elif query.data == "check_balance":
        user_id = query.from_user.id
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        message = f"""📊 <b>Balance Update</b>
        
🎯 FOMO Scans: <b>{total_free_remaining} remaining</b>
💎 FCB Tokens: <b>{fcb_balance}</b>"""
        
        await query.edit_message_text(message, parse_mode='HTML')
        return
    
    # Check if user has queries available
    allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
    
    if not allowed:
        if reason == "No queries available":
            message = format_out_of_scans_refresh_message()
            keyboard = build_out_of_scans_refresh_keyboard()
            await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
        else:
            countdown_msg = create_countdown_visual(time_remaining)
            await query.edit_message_text(countdown_msg, parse_mode='HTML')
        return
    
    # Handle Refresh button with instant response
    if query.data.startswith("refresh_"):
        coin_id = query.data.replace("refresh_", "")
        await handle_instant_update(query, context, coin_id, user_id)
    
    # Handle Next/Spin button with instant response
    elif query.data == "next_coin":
        await handle_instant_spin(query, context, user_id)
    
    else:
        logging.warning(f"UNKNOWN CALLBACK: '{query.data}'")
        await query.edit_message_text("❌ Unknown action. Please try again.", parse_mode='HTML')

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
            await query.edit_message_text("❌ Error creating invoice. Please try again.")

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
    actual_buyer_id = update.effective_user.id  # ✅ Get the actual buyer's ID
    
    # Add debug logging
    logging.info(f"🔍 PAYMENT DEBUG: Buyer ID: {actual_buyer_id}")
    logging.info(f"🔍 PAYMENT DEBUG: Payload: {payment.invoice_payload}")
    logging.info(f"🔍 PAYMENT DEBUG: Stars amount: {payment.total_amount}")
    
    # Parse payload
    payload_parts = payment.invoice_payload.split("_")
    
    if len(payload_parts) == 3 and payload_parts[0] == "fcb":
        package_key = payload_parts[1]
        payload_user_id = int(payload_parts[2])
        
        # ✅ Security check: ensure the buyer matches the payload
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
            
            # ✅ Add tokens with verification
            success, new_balance = add_fcb_tokens(actual_buyer_id, tokens)
            
            if success:
                # ✅ Record first purchase date using local import
                try:
                    from database import get_db_connection
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
                
                # ✅ Send success message with balance confirmation
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
                # ✅ Handle database failure
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
    app.add_handler(CommandHandler('buy', buy_command))
    app.add_handler(CommandHandler('debug', debug_balance_command))
    app.add_handler(CommandHandler('balance', balance_command))
    app.add_handler(CommandHandler('test', test_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('unsubscribe', unsubscribe_command))
    
    # Callback query handler for ALL buttons (purchase + addictive buttons)
    app.add_handler(CallbackQueryHandler(handle_callback_queries))
    
    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success_handler))
    
    # Main message handler for coin analysis (ULTRA-FAST)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_coin_message_ultra_fast))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logging.info("✅ All handlers setup complete")