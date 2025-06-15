"""
Message formatting module for CFB (Crypto FOMO Bot)
Handles all message formatting, keyboards, and visual elements
"""

import pytz
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re

# =============================================================================
# UTILITY FUNCTIONS FOR FORMATTING
# =============================================================================

def emoji_for_percent(val):
    """Return emoji based on percentage change"""
    try:
        val = float(val)
    except:
        val = 0
    return "🟢" if val >= 1 else "🔻" if val <= -1 else "⚪"

def short_stat(value, decimals=2, prefix='$'):
    """Format numeric values with appropriate precision"""
    try:
        if value == '?' or value is None:
            return "?"
        value = float(value)
        if value < 1:
            return f"{prefix}{value:.8f}" if prefix else f"{value:.8f}"
        else:
            return f"{prefix}{value:,.2f}" if prefix else f"{value:,.2f}"
    except:
        return "?"

def get_simple_timestamp():
    """Get simple timestamp with just UTC+5:30"""
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M')} (UTC+5:30)"

def parse_exchange_info(distribution_status):
    """Extract exchange count and top exchange percentage from distribution status"""
    try:
        # Extract percentage from strings like "✅ Good Distribution - Top exchange controls 34.5% of trading (3 total exchanges)"
        
        # Look for percentage pattern
        percent_match = re.search(r'(\d+\.?\d*)%', distribution_status)
        percent = percent_match.group(1) if percent_match else "?"
        
        # Look for exchange count pattern
        count_match = re.search(r'\((\d+) total exchanges\)', distribution_status)
        count = count_match.group(1) if count_match else "?"
        
        return count, percent
    except:
        return "?", "?"

def create_countdown_visual(seconds_remaining):
    """Create visual countdown - now much shorter due to 1-second rate limit"""
    if seconds_remaining <= 1:
        return "⚡ <b>Ready!</b>\n\nYou can send your next query now."
    else:
        return f"⏰ <b>Rate Limit</b>\n\nNext query available in {seconds_remaining} second.\n\n💡 <i>This protects our API costs!</i>"

def get_buy_coin_url(coin_data):
    """Generate tracking URL for BUY COIN button"""
    from config import SHORTIO_LINK_ID
    
    # Get coin symbol for tracking
    coin_symbol = coin_data.get('symbol', '').upper()
    coin_id = coin_data.get('id', '')
    
    # Use the tracking link from environment variables
    tracking_url = SHORTIO_LINK_ID
    
    # Add coin identifier to track which specific coin was clicked
    if coin_symbol:
        if '?' in tracking_url:
            tracking_url += f"&coin={coin_symbol}"
        else:
            tracking_url += f"?coin={coin_symbol}"
    
    return tracking_url

# =============================================================================
# MAIN MESSAGE FORMATTING FUNCTIONS
# =============================================================================

def format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status=None, distribution_status=None, is_broadcast=False):
    """Format FOMO message"""
    name = f"{coin.get('name', 'Unknown')} ({coin.get('symbol', '')})"
    price = short_stat(coin.get("price"))
    p1 = coin.get("change_1h", 0) or 0
    p24 = coin.get("change_24h", 0) or 0
    v24 = int(coin.get("volume", 0) or 0)
    
    exchange_count, top_percent = parse_exchange_info(distribution_status or "")
    header = name  # Just the coin name for both broadcast and regular messages
    
    message_parts = [
        header,
        "",
        f"<b>FOMO: {fomo_score}%</b>",
        f"<b>Current Price:</b> {price}",
        "",
        f"<b>Price:</b>",
        f"1hr: {emoji_for_percent(p1)} <b>{p1:+.1f}%</b> | 24hr: {emoji_for_percent(p24)} <b>{p24:+.1f}%</b>",
        "",
        f"<b>Volume:</b>",
        f"24hr: <b>${v24:,}</b> | Spike: <b>{volume_spike:.1f}x</b>",
        "",
        f"<b>Trend:</b> {trend_status or 'Analyzing...'}",
        "",
        f"<b>Exchanges:</b> {exchange_count} | Top controls {top_percent}%",
        "",
        "📊 <i>High FOMO = Better Odds</i>",
        "",
        "📋 T&C's in pin @freecryptopings",
    ]
    
    if is_broadcast:
        message_parts.extend([
            "",
            "🚀 <b>Ready for more FOMO analysis?</b>",
            "Start chatting with @fomocryptobot for instant insights!"
        ])
    
    if not is_broadcast:
        message_parts.extend([
            "",
            f"<i>{get_simple_timestamp()}</i>"
        ])
    
    return "\n".join(message_parts)

def format_treasure_discovery_message(coin, fomo_score, signal_type, volume_spike):
    """Format treasure discovery message"""
    name = f"{coin.get('name', 'Unknown')} ({coin.get('symbol', '')})"
    price = short_stat(coin.get("price"))
    p1 = coin.get("change_1h", 0) or 0
    p24 = coin.get("change_24h", 0) or 0
    v24 = int(coin.get("volume", 0) or 0)
    
    # Note: Remove "GOLDEN OPPORTUNITY FOUND!" - just use coin name
    message_parts = [
        f"<b>{name}</b>",  # Just the coin name, no discovery type
        "",
        f"<b>FOMO: {fomo_score}%</b>",
        f"<b>Current Price:</b> {price}",
        "",
        f"<b>Price:</b>",
        f"1hr: {emoji_for_percent(p1)} <b>{p1:+.1f}%</b> | 24hr: {emoji_for_percent(p24)} <b>{p24:+.1f}%</b>",
        "",
        f"<b>Volume:</b>",
        f"24hr: <b>${v24:,}</b> | Spike: <b>{volume_spike:.1f}x</b>",
        "",
        f"<b>Trend:</b> {signal_type}",  # Add trend below volume
        "",
        f"<b>Exchanges:</b> ? | Top controls ?%",  # Add exchanges below trend
        "",
        "👉 <i>Tap NEXT to discover more treasures!</i>",  # Replace spin message
        "",
        f"<i>{get_simple_timestamp()}</i>"
    ]
    
    return "\n".join(message_parts)

def format_balance_message(user_balance_info, conversion_hooks=True):
    """Format balance message with conversion hooks"""
    fcb_balance = user_balance_info.get('fcb_balance', 0)
    free_queries_used = user_balance_info.get('free_queries_used', 0)
    new_user_bonus_used = user_balance_info.get('new_user_bonus_used', 0)
    total_free_remaining = user_balance_info.get('total_free_remaining', 0)
    has_received_bonus = user_balance_info.get('has_received_bonus', False)
    
    from config import FREE_QUERIES_PER_DAY, NEW_USER_BONUS
    
    # Calculate breakdown
    daily_remaining = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
    bonus_remaining = max(0, NEW_USER_BONUS - new_user_bonus_used) if not has_received_bonus else 0
    
    message = f"""📊 <b>Your FOMO Scanner</b>

🎯 <b>FOMO Scans:</b> {total_free_remaining} remaining"""
    
    if bonus_remaining > 0:
        message += f"\n   ✨ Welcome bonus: {bonus_remaining} scans"
    if daily_remaining > 0:
        message += f"\n   🔄 Daily scans: {daily_remaining} left"
    
    message += f"\n💎 <b>FCB Tokens:</b> {fcb_balance}"
    
    # Add conversion hooks based on usage
    if conversion_hooks:
        if total_free_remaining <= 2:
            message += f"""

🚨 <b>Almost Out of Scans!</b>
You're about to hit your limit. Premium users never worry about running out.

💎 <b>Get Unlimited FOMO Scanning:</b>
- Scan any coin, anytime
- No daily limits or waiting
- Same algorithm as our 70%+ alerts"""
        
        elif total_free_remaining <= 5:
            message += f"""

⚠️ <b>Halfway Through Your Scans</b>
Consider upgrading before you find that next 🚀 opportunity!"""
        
        message += f"""

<b>💡 How it works:</b>
- New users: {NEW_USER_BONUS} welcome FOMO scans
- Everyone: {FREE_QUERIES_PER_DAY} daily scans  
- Premium: Unlimited with FCB tokens

📋 T&C's in pin @freecryptopings

Need more? Use /buy"""

    return message

def format_purchase_options_message(user_balance_info):
    """Format FCB token purchase options using FOMO language"""
    fcb_balance = user_balance_info.get('fcb_balance', 0)
    total_free_remaining = user_balance_info.get('total_free_remaining', 0)
    
    message = f"""⭐ <b>Get Unlimited FOMO Scanning!</b>

<b>Your Current Status:</b>
🎯 FOMO Scans: <b>{total_free_remaining} remaining</b>
💎 FCB Tokens: <b>{fcb_balance}</b>

🚨 <b>Don't miss the next moon shot!</b>

<b>💫 Pay with Telegram Stars:</b>
⭐ <b>Starter</b> - 100 Stars → 100 scans
🔥 <b>Premium</b> - 250 Stars → 250 scans <b>(MOST POPULAR)</b>
⭐ <b>Pro</b> - 500 Stars → 500 scans
⭐ <b>Elite</b> - 1,000 Stars → 1,000 scans

<b>✨ How to pay:</b>
1. Tap any package below
2. Pay instantly with Telegram Stars
3. Get FCB tokens immediately!

<b>💡 Need Stars?</b>
Settings → Stars → Buy More Stars

<b>🚀 Why upgrade?</b>
- Never run out of scans again
- ⬅️ BACK any coin anytime
- 🎰 NEXT button always works
- Same algorithm as our 70%+ alerts

📋 T&C's in pin @freecryptopings

<i>Payment processed instantly via Telegram!</i>"""

    return message

def format_out_of_scans_message(query):
    """Format message for when user is out of scans"""
    message = f"""💔 <b>FOMO Scan Limit Reached!</b>

You wanted to analyze <b>{query.upper()}</b> but you're out of scans.

😤 <b>This is frustrating, right?</b>
What if {query} is about to 🚀 and you're missing it?

💎 <b>Premium users would see:</b>
- Real-time FOMO score for {query}
- Volume spike analysis  
- ⬅️ Back & 🎰 Spin buttons
- Unlimited market scanning

🚨 <b>Don't miss the next moon shot!</b>

💫 <b>Get 100 scans for just 100 Telegram Stars!</b>
Tap below to pay instantly and never run out again."""
    
    return message

def format_out_of_scans_back_message():
    """Format message for when user is out of scans during back"""
    message = """💔 <b>Out of FOMO Scans!</b>

You wanted fresh data but you're out of scans.

🚨 <b>The market is moving fast!</b>
While you wait, opportunities might be slipping away...

💎 <b>Premium users are getting:</b>
- Real-time updates every second
- Fresh 🎰 Spin recommendations  
- Never missing a moon shot

Get unlimited scans with FCB tokens!"""

    return message

def format_payment_success_message(tokens, stars):
    """Format successful payment message"""
    message = f"""✅ <b>Payment Successful!</b>

🎫 <b>{tokens} FCB tokens</b> added to your account!
⭐ Stars spent: <b>{stars}</b>

You can now use unlimited FOMO scanning!
Just type any coin name to get started.

Thank you for supporting FOMO Crypto Bot! 🚀"""

    return message

# =============================================================================
# KEYBOARD BUILDERS
# =============================================================================

def build_addictive_buttons(coin, user_balance_info=None):
    """Create addictive buttons with tracking URL for BUY COIN"""
    # If no balance info provided, just show buttons without balance text
    balance_text = ""
    
    if user_balance_info:
        remaining = user_balance_info.get('total_free_remaining', 0)
        if remaining > 0:
            balance_text = f" ({remaining} left)"
        elif user_balance_info.get('fcb_balance', 0) > 0:
            balance_text = f" ({user_balance_info['fcb_balance']} FCB)"
        else:
            balance_text = " (0 left)"
    
    coin_id = coin.get('id', 'unknown')
    safe_coin_id = coin_id[:50] if len(coin_id) > 50 else coin_id
    back_callback = f"back_{safe_coin_id}"
    next_callback = "next_coin"
    
    # Use tracking URL for BUY COIN button
    buy_coin_url = get_buy_coin_url(coin)
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f'⬅️ BACK{balance_text}', callback_data=back_callback),
            InlineKeyboardButton(f'🎰 NEXT{balance_text}', callback_data=next_callback)
        ],
        [
            InlineKeyboardButton('💰 BUY COIN', url=buy_coin_url),
            InlineKeyboardButton('⭐ TOP UP', callback_data='buy_starter')
        ]
    ])

def build_purchase_keyboard():
    """Build purchase options keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💫 Starter (100⭐)", callback_data="buy_starter")],
        [InlineKeyboardButton("🔥 Premium (250⭐) - MOST POPULAR", callback_data="buy_premium")],
        [InlineKeyboardButton("💫 Pro (500⭐)", callback_data="buy_pro")],
        [InlineKeyboardButton("💫 Elite (1000⭐)", callback_data="buy_elite")],
        [InlineKeyboardButton("📊 Check Balance", callback_data="check_balance")]
    ])

def build_broadcast_keyboard(coin_data):
    """Build keyboard for broadcast messages with tracking URL"""
    # Use tracking URL for BUY COIN button
    buy_coin_url = get_buy_coin_url(coin_data)
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⬅️ BACK', callback_data=f"back_{coin_data.get('id', coin_data.get('coin', 'unknown'))}"),
            InlineKeyboardButton('🎰 NEXT', callback_data="next_coin")
        ],
        [
            InlineKeyboardButton('💰 BUY COIN', url=buy_coin_url),
            InlineKeyboardButton('⭐ TOP UP', callback_data='buy_starter')
        ]
    ])

def build_out_of_scans_keyboard(query):
    """Build keyboard for out of scans message"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"🚀 Analyze {query.upper()} Now!", callback_data="buy_starter")
    ]])

def build_out_of_scans_back_keyboard():
    """Build keyboard for out of scans back message"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Go Premium Now!", callback_data="buy_premium")
    ]])

# =============================================================================
# HELP AND INFO MESSAGES
# =============================================================================

def get_start_message():
    """Get welcome/start message"""
    return """👋 Welcome to <b>ULTRA-FAST FOMO Crypto Bot</b>!

🔥 <b>What I do:</b>
• Send alerts when I spot high-opportunity coins
• Provide ULTRA-FAST analysis for any coin you ask about  
• Use volume spike detection to catch coins before they moon

⚡ <b>NEW: 5x FASTER Performance!</b>
• 1-second rate limit (was 5 seconds)
• Parallel API processing
• 500 API calls/minute capacity

⏰ <b>Interactive Usage:</b>
• Type any coin name (like <code>btc</code>, <code>pepe</code>, <code>solana</code>)
• Get instant FOMO analysis with volume spike data
• Free users: Get 8 FREE FOMO scans to start!
• Premium users: Unlimited with FCB tokens

🎯 <b>FOMO Score = Moon Probability</b>
90%+ = 🚀 Very likely to pump
70%+ = ⚡ Good pump odds  
&lt;40% = 📉 Odds favor decline

<i>Same algorithm that powers our automated alerts!</i>"""

def get_help_message():
    """Get help message"""
    return """🎯 <b>ULTRA-FAST FOMO Crypto Bot Help</b>

<b>🚨 Automated Alerts:</b>
• Receive alerts every 2 hours (increased frequency)
• Only coins with 70%+ FOMO scores
• Delivered automatically when opportunities arise

<b>💬 Interactive Analysis:</b>
• Type any coin name: <code>btc</code>, <code>ethereum</code>, <code>pepe</code>
• Get ULTRA-FAST volume spike analysis (5x faster!)
• Rate limited: 1 second between queries (was 5!)

<b>🎯 Understanding FOMO Scores:</b>
• 90%+ = 🚀 Stealth accumulation detected
• 70%+ = ⚡ Early momentum building
• 50%+ = 🟡 Volume building up
• &lt;40% = 📉 Low activity

<b>💎 FCB Token Benefits:</b>
• Free: 8 FOMO scans to start (3 bonus + 5 daily)
• Premium: Unlimited scans with FCB tokens
• Instant ⬅️ Back and 🎰 Spin buttons

<b>⚡ Performance Improvements:</b>
• 500 API calls/minute (10x more capacity)
• Parallel processing (3x faster analysis)
• Burst rate limiting (instant first 10 calls)
• Optimized connection pooling

📋 T&C's in pin @freecryptopings"""