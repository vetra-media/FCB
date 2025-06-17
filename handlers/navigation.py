"""
handlers/navigation.py - Navigation Logic (BACK/NEXT buttons)
Handles FREE back navigation and smart NEXT logic
"""

import logging
import time
from io import BytesIO

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Core imports
from .core import (
    get_user_session, get_cached_coin_data, add_to_user_history,
    debug_user_session, validate_coingecko_id, get_clean_balance_display,
    get_user_balance_info, safe_edit_message
)

from database import get_user_balance, spend_fcb_token, check_rate_limit_with_fcb
from api_client import get_coin_info_ultra_fast, get_optimized_session
from analysis import calculate_fomo_status_ultra_fast

from formatters import (
    format_simple_message, build_addictive_buttons,
    format_out_of_scans_message, build_out_of_scans_keyboard,
    format_out_of_scans_back_message_with_navigation,
    build_out_of_scans_back_keyboard_with_navigation,
    create_countdown_visual
)

from .discovery import handle_instant_discovery

# =============================================================================
# BACK Navigation - ALWAYS FREE with Smart Caching
# =============================================================================

async def handle_back_navigation(query, context, user_id):
    """
    Handle BACK button with ALWAYS FREE navigation
    Uses cached data when available, minimal API calls only when absolutely necessary
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
                
                # Create clean image caption vs detailed text message
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
                
                # Handle logo display with clean captions
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
                                    # Use clean_caption for image (no navigation noise)
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
        
        # Enhanced message formatting with clean image vs detailed text separation
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
        
        # Handle logo updates with clean captions
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
                            # Use clean_caption for image (no navigation noise)
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
# Forward Navigation Helper with Smart Caching
# =============================================================================

async def display_coin_from_history_forward(query, context, user_id, target_coin_id, cached_coin=None, from_alert=False):
    """
    Display a coin from history for forward navigation
    Uses cached data when available, minimal API calls when necessary
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
    
    # Create separate clean caption vs detailed message
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
    
    # Display with photo using CLEAN caption
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
                        # Use clean_caption for image (NO navigation noise!)
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