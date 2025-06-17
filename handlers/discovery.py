"""
handlers/discovery.py - Coin Analysis & Discovery
Main message handler and opportunity discovery logic
"""

import logging
import random
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

# Core imports
from .core import (
    get_user_session, get_cached_coin_data, add_to_user_history,
    debug_user_session, validate_coingecko_id, get_clean_balance_display,
    get_user_balance_info, safe_edit_message, hunt_next_opportunity,
    OPPORTUNITY_HUNTER_CONFIG
)

from database import (
    get_user_balance, spend_fcb_token, check_rate_limit_with_fcb
)

from config import FOMO_CACHE
from api_client import get_coin_info_ultra_fast, get_optimized_session
from analysis import calculate_fomo_status_ultra_fast
from cache import get_ultra_fast_fomo_opportunities

from formatters import (
    format_simple_message, format_treasure_discovery_message,
    format_out_of_scans_message_with_back, format_out_of_scans_back_message_with_navigation,
    build_addictive_buttons, build_out_of_scans_keyboard_with_back,
    build_out_of_scans_back_keyboard_with_navigation, create_countdown_visual
)

# =============================================================================
# Smart Opportunity Discovery with Proper Token Management
# =============================================================================

async def handle_instant_discovery(query, context, user_id, force_new=True):
    """
    Opportunity discovery with proper token management
    force_new=True means this costs a token (new API call)
    force_new=False means try to use cached data first
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
        if not FOMO_CACHE['coins']:
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
                    # Update logo URL from fresh API data if available
                    if test_coin.get('logo'):
                        coin['logo'] = test_coin['logo']
            except Exception:
                pass
            
            new_coin_id = proper_coin_id if proper_coin_id else raw_coin_id
            
            # Add to navigation history with cached data
            coin['id'] = new_coin_id
            session = add_to_user_history(user_id, new_coin_id, coin_data=coin)
            
            # Create clean image caption vs detailed text message
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
            
            # Handle logo display with clean captions
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
                                # Use clean_caption for image (no cost noise)
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
# Enhanced Coin Analysis with Proper Token Management
# =============================================================================

async def send_coin_message_ultra_fast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main coin analysis handler with proper token spending
    Only costs tokens for fresh API calls, not for system operations
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
        
        # Create clean image caption vs detailed text message
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
        
        # Try with logo for visual appeal with clean caption
        logo_url = coin.get('logo')
        photo_sent = False
        
        if logo_url:
            try:
                api_session = await get_optimized_session()
                async with api_session.get(logo_url) as response:
                    if response.status == 200:
                        image_bytes = BytesIO(await response.read())
                        # Use clean_caption for image (no cost noise)
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
# Alert Coin Handler with Proper Economics
# =============================================================================

async def handle_alert_coin_analysis(user_id, coin_id, context, original_message=None):
    """
    Special handler for when users click alert buttons
    First tries cached data, falls back to fresh API call if needed
    """
    
    logging.info(f"🔥 Alert coin analysis: User {user_id} analyzing {coin_id}")
    
    # Try to use cached data first
    cached_coin = get_cached_coin_data(user_id, coin_id)
    
    if cached_coin:
        logging.info(f"🆓 Using cached data for alert navigation: {coin_id}")
        
        # Use cached data - no API call needed
        try:
            # Create clean image caption vs detailed text message
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
        
        # Create clean image caption vs detailed text message
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
# Buy Coin Button Handler
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
        from formatters import get_buy_coin_url
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
            from .callbacks import handle_back_to_main
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
            from .callbacks import handle_back_to_main
            await handle_back_to_main(query, context, user_id)
            
    except Exception as e:
        logging.error(f"Error in back to analysis: {e}")
        from .callbacks import handle_back_to_main
        await handle_back_to_main(query, context, user_id)