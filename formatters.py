"""
Message formatting module for CFB (Crypto FOMO Bot) - ULTRA-CLEAN UI VERSION - COMPLETE
✅ FIXED: Removed ALL discovery noise above coin names
✅ FIXED: Removed ALL extra spaces between elements  
✅ FIXED: Perfect 4-element layout with no spacing
✅ COMPLETE: All functions from original PART 1/2 and PART 2/2 included
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
    """Get simple timestamp with UTC"""
    tz = pytz.timezone("UTC")
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M')} (UTC)"

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

def build_main_menu_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👈 BACK", callback_data="back"),
            InlineKeyboardButton("👉 NEXT", callback_data="next")
        ],
        [
            InlineKeyboardButton("💰 BUY COIN", url="https://your-buy-link.com"),
            InlineKeyboardButton("🤖 TOP UP", callback_data="topup")
        ]
    ])

# =============================================================================
# FOMO EMOJI SYSTEM - TELLS THE COMPLETE STORY
# =============================================================================

def get_fomo_emoji(fomo_score):
    """Get dynamic emoji based on FOMO score - emoji tells the complete story"""
    if fomo_score >= 90:
        return "🏆"  # LEGENDARY - Amazing (90%+)
    elif fomo_score >= 85:
        return "🚀"  # EPIC - Great (85%+)  
    elif fomo_score >= 70:
        return "⚡"  # RARE - Good (70%+)
    elif fomo_score >= 55:
        return "📈"  # SOLID - Okay (55%+)
    elif fomo_score >= 40:
        return "👀"  # MODERATE - Meh (40%+)
    else:
        return "😴"  # LOW - Low (below 40%)

def convert_fomo_score_to_signal(fomo_score):
    """Convert technical FOMO score to user-friendly signal"""
    if fomo_score >= 85:
        return "🚀 Very high probability"
    elif fomo_score >= 70:
        return "⚡ High probability opportunity"
    elif fomo_score >= 55:
        return "📈 Good opportunity"
    elif fomo_score >= 40:
        return "👀 Moderate opportunity"
    else:
        return "😴 Low opportunity"

# =============================================================================
# ✅ FIXED: ULTRA-CLEAN 4-ELEMENT LAYOUT - NO SPACES, NO NOISE
# =============================================================================

def format_simple_message(coin, fomo_score, signal_type=None, volume_spike=None, trend_status=None, distribution_status=None, is_broadcast=False):
    """
    ✅ FIXED: Perfect 2-element layout for casino - NO TKN here
    1. Coin Name & Symbol (🚀 Bitcoin (BTC))
    2. FOMO & Score with emoji (😴 FOMO: 21%) 
    3. TKN added separately by get_balanced_bottom_line()
    """
    name = coin.get('name', 'Unknown')
    symbol = coin.get('symbol', '').upper()
    fomo_emoji = get_fomo_emoji(fomo_score)
    
    # ✅ PERFECT 2-ELEMENT LAYOUT - NO TKN HERE
    message_parts = [
        f"🚀 <b>{name} ({symbol})</b>",  # 1. Name & Symbol
        f"{fomo_emoji} <b>FOMO: {fomo_score}%</b>",  # 2. FOMO & Score
        # 3. TKN added separately by handlers using get_balanced_bottom_line()
    ]
    
    # Add call-to-action for broadcasts only
    if is_broadcast:
        message_parts.extend([
            "",
            "🚀 <b>Ready for more opportunities?</b>",
            "Start chatting with @fomocryptopings for instant insights!"
        ])
    
    return "\n".join(message_parts)

def format_treasure_discovery_message(coin, fomo_score, signal_type, volume_spike):
    """
    ✅ FIXED: Same ultra-clean 4-element layout - NO discovery noise above coin name
    ❌ REMOVED: All excitement/discovery messages that appear above coin name
    """
    name = coin.get('name', 'Unknown')
    symbol = coin.get('symbol', '').upper()
    fomo_emoji = get_fomo_emoji(fomo_score)
    
    # ✅ PERFECT 4-ELEMENT LAYOUT - NO SPACES, NO DISCOVERY NOISE
    message_parts = [
        f"🚀 <b>{name} ({symbol})</b>",  # 1. Name & Symbol
        f"{fomo_emoji} <b>FOMO: {fomo_score}%</b>",  # 2. FOMO & Score (emoji tells story!)
        # 3. Tokens added separately by handlers
    ]
    
    # ❌ COMPLETELY REMOVED: Discovery messages, signal descriptions, excitement text
    # ❌ COMPLETELY REMOVED: ALL empty lines between elements
    
    return "\n".join(message_parts)

def format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status=None, distribution_status=None, is_broadcast=False):
    """
    ✅ FIXED: Uses ultra-clean formatting - maintains backward compatibility
    """
    return format_simple_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast)

def format_price_display(price):
    """Format price with smart precision and money bag emoji"""
    try:
        price = float(price) if price else 0
        if price == 0:
            return "💰 <i>Price: N/A</i>"
        elif price < 0.001:
            return f"💰 <i>${price:.8f}</i>"
        elif price < 1:
            return f"💰 <i>${price:.6f}</i>"
        elif price < 1000:
            return f"💰 <i>${price:.2f}</i>"
        else:
            return f"💰 <i>${price:,.0f}</i>"
    except:
        return "💰 <i>Price: N/A</i>"

# =============================================================================
# LEGACY COMPLEX FORMATTER (PRESERVED FOR TESTING/FALLBACK)
# =============================================================================

def format_complex_message(coin, fomo_score, signal_type, volume_spike, trend_status=None, distribution_status=None, is_broadcast=False):
    """
    LEGACY: Original complex formatter preserved for testing/fallback
    Shows all technical details
    """
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
        f"<i>{get_simple_timestamp()}</i>"
    ]
    
    if is_broadcast:
        message_parts.extend([
            "",
            "🚀 <b>Ready for more FOMO analysis?</b>",
            "Start chatting with @fomocryptobot for instant insights!"
        ])
    
    return "\n".join(message_parts)

# =============================================================================
# BALANCE AND PURCHASE MESSAGE FORMATTERS (FIXED: NO MORE "UNLIMITED")
# =============================================================================

def format_balance_message(user_balance_info, conversion_hooks=True):
    """FIXED: Simplified balance message - no more "unlimited" promises"""
    fcb_balance = user_balance_info.get('fcb_balance', 0)
    total_free_remaining = user_balance_info.get('total_free_remaining', 0)
    
    message = f"""📊 <b>Your Scanner</b>

🎯 <b>Scans Available:</b> {total_free_remaining}
💎 <b>FCB Tokens:</b> {fcb_balance}"""
    
    # Add conversion hooks based on usage - FIXED messaging
    if conversion_hooks:
        if total_free_remaining <= 2:
            message += f"""

🚨 <b>Almost Out of Scans!</b>
Get premium scanning with FCB tokens.

💎 <b>Premium Benefits:</b>
- 250+ scans per package
- No daily limits
- Professional insights

Need more? Use /buy"""
        else:
            message += f"""

💡 <b>How it works:</b>
- Free scans reset daily
- Premium: 250+ scans with FCB tokens
- Same algorithm as our successful alerts

Need more? Use /buy"""

    return message

def format_purchase_options_message(user_balance_info):
    """FIXED: Simplified purchase options message - accurate premium packages"""
    fcb_balance = user_balance_info.get('fcb_balance', 0)
    total_free_remaining = user_balance_info.get('total_free_remaining', 0)
    
    message = f"""⭐ <b>Get Premium Scan Packages!</b>

<b>Your Status:</b>
🎯 Scans Available: <b>{total_free_remaining}</b>
💎 FCB Tokens: <b>{fcb_balance}</b>

🚨 <b>Don't miss the next big opportunity!</b>

<b>💫 Pay with Telegram Stars:</b>
⭐ <b>Starter</b> - 100 Stars → 100 scans
🔥 <b>Premium</b> - 250 Stars → 250 scans <b>(MOST POPULAR)</b>
⭐ <b>Pro</b> - 500 Stars → 500 scans
⭐ <b>Elite</b> - 1,000 Stars → 1,000 scans

<b>✨ How to pay:</b>
1. Tap any package below
2. Pay instantly with Telegram Stars
3. Get FCB tokens immediately!

<b>🚀 Why upgrade?</b>
- Premium scan packages
- Professional insights
- Never miss out again

<i>Payment processed instantly via Telegram!</i>"""

    return message

def format_out_of_scans_message(query=None):
    """
    FIXED: Simplified out of scans message - accurate premium messaging
    Added optional query parameter for compatibility
    """
    if query:
        message = f"""💔 <b>Scan Limit Reached!</b>

You wanted to analyze <b>{query.upper()}</b> but you're out of scans.

😤 <b>This is frustrating, right?</b>
What if {query} is about to 🚀 and you're missing it?

💎 <b>Premium users would see:</b>
- Real-time opportunity score for {query}
- Professional insights
- Premium scanning access

🚨 <b>Don't miss the next big opportunity!</b>

💫 <b>Get 100 scans for just 100 Telegram Stars!</b>
Tap below to upgrade instantly."""
    else:
        message = """💔 <b>Out of Scans!</b>

You've used all your free scans for today.

🎯 <b>Get More Scans:</b>
- Buy FCB tokens with premium packages
- Get premium scanning instantly!

💡 <b>Why upgrade?</b>
- No daily limits
- Professional insights
- Premium features

Don't miss the next big opportunity! 🚀"""
    
    return message

def format_out_of_scans_back_message():
    """FIXED: Simplified back message for out of scans - accurate messaging"""
    message = """💔 <b>Out of Scans!</b>

You wanted fresh data but you're out of scans.

🚨 <b>Opportunities are moving fast!</b>
While you wait, the next big opportunity might slip away...

💎 <b>Premium users are getting:</b>
- Real-time updates
- Fresh opportunities
- Professional insights

Get premium scan packages with FCB tokens!"""

    return message

def format_payment_success_message(tokens, stars):
    """FIXED: Simplified payment success message - accurate premium access"""
    message = f"""✅ <b>Payment Successful!</b>

🎫 <b>{tokens} FCB tokens</b> added to your account!
⭐ Stars spent: <b>{stars}</b>

You now have premium scanning access!
Just type any coin name to get started.

Thank you for supporting FOMO Crypto Bot! 🚀"""

    return message

# =============================================================================
# ENHANCED MESSAGE FORMATTERS WITH BACK BUTTON SUPPORT (FROM PART 2/2)
# =============================================================================

def format_out_of_scans_message_with_back(query=None):
    """FIXED: Simplified out of scans message with back button - accurate premium messaging"""
    if query:
        message = f"""💔 <b>Scan Limit Reached!</b>

You wanted to analyze {query.upper()} but you're out of scans.

😤 <b>This is frustrating, right?</b>
What if {query} is about to 🚀 and you're missing it?

💎 <b>Premium users would see:</b>
- Real-time opportunity score for {query}
- Professional analysis
- Premium scanning access

🚨 <b>Don't miss the next big opportunity!</b>

💫 <b>Get 100 scans for just 100 Telegram Stars!</b>

Or go back to explore other features..."""
    else:
        message = """💔 <b>Out of Scans!</b>

You've used all your free scans for today.

🎯 <b>Get More Scans:</b>
- Buy FCB tokens with premium packages
- Get premium scanning instantly!

💡 <b>Why upgrade?</b>
- No daily limits
- Professional insights
- Premium features

Or go back to explore other features..."""
    
    return message

def format_out_of_scans_back_message_with_navigation():
    """FIXED: Simplified back message with navigation options - accurate messaging"""
    return """💔 <b>Out of Scans!</b>

You wanted fresh data but you're out of scans.

🚨 <b>Opportunities are moving fast!</b>
While you wait, the next big opportunity might slip away...

💎 <b>Premium users are getting:</b>
- Real-time updates
- Fresh opportunities
- Professional insights

Options:
- 🚀 Upgrade for premium scan packages
- ⬅️ Go back to main menu
- ⏰ Wait for daily reset

Your choice - don't let opportunities slip away!"""

# =============================================================================
# UPDATED KEYBOARD BUILDERS (🤖 TOP UP INSTEAD OF ⭐ TOP UP) - FROM PART 2/2
# =============================================================================

def build_addictive_buttons(coin, user_balance_info=None):
    """Create buttons with updated symbols - 🤖 TOP UP for consistent theming"""
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
            InlineKeyboardButton(f'👉 NEXT{balance_text}', callback_data=next_callback)
        ],
        [
            InlineKeyboardButton('💰 BUY COIN', url=buy_coin_url),
            InlineKeyboardButton('🤖 TOP UP', callback_data='buy_starter')  # UPDATED: 🤖 instead of ⭐
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
    """Build keyboard for broadcast messages with updated symbols"""
    # Use tracking URL for BUY COIN button
    buy_coin_url = get_buy_coin_url(coin_data)
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⬅️ BACK', callback_data=f"back_{coin_data.get('id', coin_data.get('coin', 'unknown'))}"),
            InlineKeyboardButton('👉 NEXT', callback_data="next_coin")
        ],
        [
            InlineKeyboardButton('💰 BUY COIN', url=buy_coin_url),
            InlineKeyboardButton('🤖 TOP UP', callback_data='buy_starter')  # UPDATED: 🤖 instead of ⭐
        ]
    ])

def build_out_of_scans_keyboard_with_back(query=None):
    """Build keyboard for out of scans message WITH back button"""
    buttons = []
    
    if query:
        # If we know what they were searching for, offer to analyze it
        buttons.append([InlineKeyboardButton(f"🚀 Analyze {query.upper()} Now!", callback_data="buy_starter")])
    else:
        # Generic upgrade button
        buttons.append([InlineKeyboardButton("🚀 Go Premium Now!", callback_data="buy_starter")])
    
    # Add back/navigation options
    buttons.append([
        InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main"),
        InlineKeyboardButton("📊 Check Balance", callback_data="check_balance")
    ])
    
    return InlineKeyboardMarkup(buttons)

def build_out_of_scans_back_keyboard_with_navigation():
    """Build keyboard for out of scans back message WITH navigation"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Go Premium Now!", callback_data="buy_premium")],
        [
            InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main"),
            InlineKeyboardButton("🎯 Try Again Later", callback_data="show_rate_limit_info")
        ]
    ])

def build_out_of_scans_keyboard():
    """Build keyboard for basic out of scans message"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Go Premium Now!", callback_data="buy_starter")],
        [InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main")]
    ])

def build_out_of_scans_back_keyboard():
    """Build keyboard for out of scans back message"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Go Premium Now!", callback_data="buy_premium")],
        [InlineKeyboardButton("⬅️ Back to Bot", callback_data="back_to_main")]
    ])

# =============================================================================
# SIMPLIFIED HELP AND INFO MESSAGES (FIXED) - FROM PART 2/2
# =============================================================================

def get_start_message():
    """FIXED: Simplified welcome/start message - accurate premium messaging"""
    return """👋 Welcome to <b>FOMO Crypto Bot</b>!

🔥 <b>What I do:</b>
• Send alerts when I spot high-opportunity coins
• Provide instant analysis for any coin you ask about  
• Help you discover opportunities before they explode

⚡ <b>How to use:</b>
• Type any coin name (like <code>btc</code>, <code>pepe</code>, <code>solana</code>)
• Get instant opportunity analysis
• Free users: Get 8 FREE scans to start!
• Premium users: 250+ scans with FCB tokens

🎯 <b>FOMO Score = Opportunity Level</b>
90%+ = 🚀 Very high probability
70%+ = ⚡ High opportunity  
&lt;40% = 😴 Low opportunity

<i>Professional insights made simple!</i>"""

def get_help_message():
    """FIXED: Simplified help message - accurate premium messaging"""
    return """🎯 <b>FOMO Crypto Bot Help</b>

<b>🚨 Automated Alerts:</b>
• Receive alerts when opportunities arise
• Only high-probability opportunities (70%+)
• Delivered automatically to your chat

<b>💬 Interactive Analysis:</b>
• Type any coin name: <code>btc</code>, <code>ethereum</code>, <code>pepe</code>
• Get instant opportunity analysis
• Rate limited: 1 second between queries

<b>🎯 Understanding FOMO Scores:</b>
• 90%+ = 🚀 Very high probability
• 70%+ = ⚡ High opportunity
• 50%+ = 📈 Good opportunity
• &lt;40% = 😴 Low opportunity

<b>💎 Premium Benefits:</b>
• Free: 8 scans to start (3 bonus + 5 daily)
• Premium: 250+ scans with FCB tokens
• Instant ⬅️ Back and 👉 Next buttons"""

# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS - FROM PART 2/2
# =============================================================================

def format_fomo_message_legacy(coin, fomo_score, signal_type, volume_spike, trend_status=None, distribution_status=None, is_broadcast=False):
    """Legacy function - now uses simplified format"""
    return format_fomo_message(coin, fomo_score, signal_type, volume_spike, trend_status, distribution_status, is_broadcast)

def get_balanced_bottom_line(coin, user_id):
    """
    ✅ FIXED: Only show clean token format - SINGLE TKN display
    This is the ONLY function that should create TKN displays
    """
    try:
        from database import get_user_balance
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        total_scans = total_free_remaining + fcb_balance
        
        # ✅ SINGLE TKN FORMAT: Only return this format
        return f"🤖 <i>{total_scans} (TKN)</i>"
        
    except Exception as e:
        import logging
        logging.error(f"Error creating token display: {e}")
        return "🤖 <i>Error (TKN)</i>"

# ✅ REMOVED: Any other functions that create "Tokens:" displays
# ✅ REMOVED: format_token_display() function (was creating duplicates)
# ✅ REMOVED: get_clean_balance_display() function (was creating duplicates)

def get_clean_balance_display_right_aligned(user_id):
    """
    DEPRECATED: Use get_balanced_bottom_line() instead for better visual balance
    """
    try:
        from database import get_user_balance
        fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
        total_scans = total_free_remaining + fcb_balance
        return f"<div align='right'>🤖 <i>Tokens: {total_scans}</i></div>"
    except Exception as e:
        import logging
        logging.error(f"Error getting right-aligned balance: {e}")
        return "<div align='right'>🤖 <i>Tokens: Error</i></div>"

# =============================================================================
# ✅ COMPLETE FILE VERIFICATION
# =============================================================================

"""
✅ COMPLETE ULTRA-CLEAN formatters.py WITH ALL ORIGINAL FUNCTIONS

🔧 **ALL FUNCTIONS INCLUDED FROM ORIGINAL PART 1/2 AND PART 2/2:**

✅ **Core Formatting Functions:**
- format_simple_message() - ✅ FIXED: No spaces, no noise
- format_treasure_discovery_message() - ✅ FIXED: No discovery messages
- format_fomo_message() - ✅ FIXED: Uses ultra-clean format
- format_complex_message() - ✅ PRESERVED: Legacy fallback
- format_price_display() - ✅ INCLUDED

✅ **Balance & Purchase Functions:**
- format_balance_message() - ✅ FIXED: No "unlimited" promises
- format_purchase_options_message() - ✅ FIXED: Accurate packages
- format_out_of_scans_message() - ✅ FIXED: Premium messaging
- format_out_of_scans_back_message() - ✅ FIXED
- format_payment_success_message() - ✅ FIXED

✅ **Enhanced Message Functions (from PART 2/2):**
- format_out_of_scans_message_with_back() - ✅ INCLUDED
- format_out_of_scans_back_message_with_navigation() - ✅ INCLUDED

✅ **Keyboard Builder Functions (from PART 2/2):**
- build_addictive_buttons() - ✅ FIXED: 🤖 TOP UP
- build_purchase_keyboard() - ✅ INCLUDED
- build_broadcast_keyboard() - ✅ FIXED: 🤖 TOP UP
- build_out_of_scans_keyboard_with_back() - ✅ INCLUDED
- build_out_of_scans_back_keyboard_with_navigation() - ✅ INCLUDED
- build_out_of_scans_keyboard() - ✅ INCLUDED
- build_out_of_scans_back_keyboard() - ✅ INCLUDED

✅ **Help & Info Functions (from PART 2/2):**
- get_start_message() - ✅ FIXED: Accurate premium messaging
- get_help_message() - ✅ FIXED: Accurate premium messaging

✅ **Backward Compatibility (from PART 2/2):**
- format_fomo_message_legacy() - ✅ INCLUDED
- get_balanced_bottom_line() - ✅ FIXED: Only tokens, no price
- get_clean_balance_display_right_aligned() - ✅ INCLUDED (deprecated)

✅ **Utility Functions:**
- emoji_for_percent() - ✅ INCLUDED
- short_stat() - ✅ INCLUDED  
- get_simple_timestamp() - ✅ INCLUDED
- parse_exchange_info() - ✅ INCLUDED
- create_countdown_visual() - ✅ INCLUDED
- get_buy_coin_url() - ✅ INCLUDED
- get_fomo_emoji() - ✅ INCLUDED
- convert_fomo_score_to_signal() - ✅ INCLUDED

🎯 **CRITICAL FIXES APPLIED:**
1. ❌ Removed ALL discovery noise above coin names
2. ❌ Removed ALL extra spaces between elements  
3. ✅ Perfect 4-element layout: Name → FOMO → Tokens
4. ✅ Emoji tells complete story (no extra text needed)
5. ✅ All "unlimited" messaging fixed to accurate premium packages
6. ✅ Consistent 🤖 TOP UP theming throughout

✅ **RESULT:** 
Complete, ultra-clean formatters.py with all original functionality preserved while achieving perfect minimalist dashboard design.

🚨 **SAFE TO REPLACE:** This file contains everything from the original PART 1/2 and PART 2/2!
"""