"""
handlers/callbacks.py - Callback Query Router
Central routing for all button callbacks with proper economics
"""

import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Core imports
from .core import (
    get_user_session, get_cached_coin_data, add_alert_coin_to_history,
    extract_coin_id_from_alert_message, get_user_balance_info,
    safe_edit_message
)

from database import get_user_balance, check_rate_limit_with_fcb

from formatters import (
    format_out_of_scans_back_message_with_navigation,
    build_out_of_scans_back_keyboard_with_navigation,
    create_countdown_visual
)

# Import handlers from other modules
from .navigation import handle_back_navigation, handle_next_navigation
from .discovery import handle_buy_coin_button, handle_back_to_analysis, handle_alert_coin_analysis
from .payments import handle_star_purchase

# =============================================================================
# Menu Helpers with Economics Info
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
    """Handle test alert system button from main menu"""
    
    # Import here to avoid circular imports
    from .commands import test_command
    
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
    """Show rate limit information with accurate economics explanation"""
    
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
    """Show help information with accurate economics explanation"""
    
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

    elif query.data == "start_scan":
        # Handle the "Start Scanning" button from welcome screen
        from .discovery import handle_instant_discovery
        await handle_instant_discovery(query, context, user_id, force_new=True)
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
        
        # Enhanced balance message with accurate economics
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
    elif query.data == "next_coin":
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