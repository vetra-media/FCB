"""
handlers/utils.py - Utility Command Handlers
Test, status, debug, and administrative commands
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Import from other modules
from formatters import format_simple_message, build_addictive_buttons
from scanner import subscribed_users, save_subscriptions

# Import from core utilities
from .core import add_to_user_history, user_sessions

# =============================================================================
# TEST AND STATUS COMMANDS
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

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status and subscriber count"""
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
• `/start` - Subscribe to alerts  
• `/test` - Test alert with working buttons
• `/status` - Show this status
• `/unsubscribe` - Stop alerts
• `/buy` - Purchase FCB tokens
• `/balance` - Check your balance

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
# DEBUG COMMANDS
# =============================================================================

async def debug_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check user session state"""
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
# UTILITY COMMAND REGISTRY
# =============================================================================

UTILITY_COMMANDS = {
    'test': test_command,
    'status': status_command,
    'unsubscribe': unsubscribe_command,
    'debugsession': debug_session_command
}