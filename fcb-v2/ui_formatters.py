"""
FCB v2 UI Formatters
Clean, simple UI formatting matching FCB v1 design
"""

import logging
from typing import Dict, Any, Optional
from token_economics import get_user_balance_info

logger = logging.getLogger(__name__)

# =============================================================================
# COIN DISPLAY FORMATTING
# =============================================================================

def format_coin_display(coin_data: Dict, user_id: int) -> str:
    """
    Format coin data to match FCB v1 clean design
    """
    try:
        # Get balance for tokens display
        balance_info = get_user_balance_info(user_id)
        
        # Extract coin information
        symbol = coin_data.get('symbol', 'UNKNOWN').upper()
        name = coin_data.get('name', 'Unknown Coin')
        fomo_score = coin_data.get('elite_score', coin_data.get('fomo_score', 0))
        
        # Create clean display message matching original design
        display_text = f"🚀 **{name} ({symbol})**\n\n"
        display_text += f"**FOMO: {fomo_score:.2f}%**\n"
        display_text += f"⚡ High probability opportunity\n\n"
        display_text += f"🤖 Tokens: {balance_info['total_scans']}"
        
        return display_text
        
    except Exception as e:
        logger.error(f"Error formatting coin display: {e}")
        return "❌ Error displaying coin information"

def format_out_of_scans_message(user_id: int) -> str:
    """
    Format out of scans message matching FCB v1 design
    """
    try:
        balance_info = get_user_balance_info(user_id)
        
        message = "💔 **Out of Scans!**\n\n"
        message += "You wanted fresh data but you're out of scans.\n\n"
        message += "📈 Opportunities are moving fast!"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting out of scans message: {e}")
        return "💔 Out of scans! Use /buy to get more."

# =============================================================================
# BUTTON TEXT FORMATTING
# =============================================================================

def format_navigation_button_text(button_type: str, scans_remaining: int, has_history: bool = False) -> str:
    """
    Format button text to match FCB v1 simple design
    """
    if button_type == "back":
        return f"⬅️ BACK ({scans_remaining} left)"
    elif button_type == "next":
        if has_history:
            return f"➡️ NEXT ({scans_remaining} left)"
        else:
            # New discovery will cost 1 scan
            scans_after = max(0, scans_remaining - 1)
            return f"➡️ NEXT ({scans_after} left)"
    elif button_type == "buy_coin":
        return "💲 BUY COIN"
    elif button_type == "top_up":
        return "🤖 TOP UP"
    else:
        return "❌ Error"

def format_balance_display(user_id: int) -> str:
    """
    Format balance display to match FCB v1 simple format
    """
    try:
        balance_info = get_user_balance_info(user_id)
        return f"🤖 Tokens: {balance_info['total_scans']}"
    except Exception as e:
        logger.error(f"Error formatting balance display: {e}")
        return "🤖 Tokens: Error"

# =============================================================================
# MESSAGE FORMATTING
# =============================================================================

def format_welcome_message(user_name: str, balance_info: Dict) -> str:
    """
    Format welcome message matching FCB v1 style
    """
    welcome_text = f"🤖 **Welcome to FCB, {user_name}!**\n\n"
    welcome_text += "🚀 **Your Premium Crypto Scanner**\n\n"
    welcome_text += f"🤖 Tokens: {balance_info['total_scans']}\n\n"
    welcome_text += "Ready to find the next 100x? 🔥"
    
    return welcome_text

def format_purchase_success_message(tokens_added: int, total_scans: int) -> str:
    """
    Format purchase success message
    """
    message = "🎉 **Payment Successful!**\n\n"
    message += f"💰 {tokens_added} FCB tokens added!\n"
    message += f"🤖 Total tokens: {total_scans}\n\n"
    message += "Ready to scan! 🚀"
    
    return message

def format_coin_analysis_message(coin_data: Dict) -> str:
    """
    Format coin analysis to match FCB v1 clean style
    """
    try:
        symbol = coin_data.get('symbol', 'UNKNOWN').upper()
        name = coin_data.get('name', 'Unknown Coin')
        fomo_score = coin_data.get('elite_score', coin_data.get('fomo_score', 0))
        price = coin_data.get('price', 0)
        market_cap = coin_data.get('market_cap', 0)
        
        # Create clean analysis message
        analysis = f"🚀 **{name} ({symbol})**\n\n"
        analysis += f"💰 **Price:** ${price:.6f}\n"
        analysis += f"📊 **Market Cap:** ${market_cap:,.0f}\n"
        analysis += f"🔥 **FOMO Score:** {fomo_score:.2f}%\n\n"
        
        if fomo_score >= 80:
            analysis += "⚡ **High probability opportunity**"
        elif fomo_score >= 60:
            analysis += "🎯 **Good opportunity**"
        else:
            analysis += "📈 **Moderate opportunity**"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error formatting coin analysis: {e}")
        return "❌ Error analyzing coin"

# =============================================================================
# CLEAN UI HELPERS
# =============================================================================

def get_simple_coin_emoji(symbol: str) -> str:
    """
    Get simple emoji for coin display
    """
    symbol = symbol.upper()
    
    # Common coins with specific emojis
    coin_emojis = {
        'BTC': '₿',
        'ETH': '🔷',
        'BNB': '🟡',
        'ADA': '🔵',
        'SOL': '🟣',
        'DOGE': '🐕',
        'SHIB': '🐕',
    }
    
    return coin_emojis.get(symbol, '🚀')

def format_price_change(price_change_24h: float) -> str:
    """
    Format price change with appropriate emoji
    """
    if price_change_24h > 0:
        return f"📈 +{price_change_24h:.2f}%"
    elif price_change_24h < 0:
        return f"📉 {price_change_24h:.2f}%"
    else:
        return f"➡️ {price_change_24h:.2f}%"

def truncate_address(address: str, start_chars: int = 6, end_chars: int = 4) -> str:
    """
    Truncate crypto address for clean display
    """
    if not address or len(address) <= start_chars + end_chars:
        return address
    
    return f"{address[:start_chars]}...{address[-end_chars:]}"

# =============================================================================
# COMMAND RESPONSE FORMATTING
# =============================================================================

def format_balance_command_response(user_id: int) -> str:
    """
    Format /balance command response matching FCB v1 style
    """
    try:
        balance_info = get_user_balance_info(user_id)
        
        response = "🤖 **Your FCB Balance**\n\n"
        response += f"💰 **FCB Tokens:** {balance_info['fcb_balance']}\n"
        response += f"🆓 **Free Scans:** {balance_info['total_free_remaining']}\n"
        response += f"🤖 **Total Available:** {balance_info['total_scans']}\n\n"
        
        if balance_info['total_scans'] == 0:
            response += "🚨 **Out of scans!** Use /buy to get more."
        elif balance_info['total_scans'] < 5:
            response += "⚠️ **Low balance.** Consider getting more with /buy"
        else:
            response += "✅ **Ready to scan!**"
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting balance response: {e}")
        return "❌ Error loading balance. Try /balance again."

def format_help_command_response() -> str:
    """
    Format /help command response matching FCB v1 style
    """
    help_text = "❓ **FCB Help**\n\n"
    help_text += "🤖 **Commands:**\n"
    help_text += "• `/start` - Welcome & setup\n"
    help_text += "• `/scan` - Find opportunities\n"
    help_text += "• `/balance` - Check tokens\n"
    help_text += "• `/buy` - Get more tokens\n"
    help_text += "• `/help` - This guide\n\n"
    help_text += "🧭 **Navigation:**\n"
    help_text += "• BACK - Previous coins (free)\n"
    help_text += "• NEXT - New opportunities (1 token)\n"
    help_text += "• BUY COIN - Trading info\n"
    help_text += "• TOP UP - Get more tokens\n\n"
    help_text += "💰 **Token Economics:**\n"
    help_text += "• 5 free scans daily\n"
    help_text += "• 3 bonus scans for new users\n"
    help_text += "• Buy FCB tokens for unlimited scanning\n\n"
    help_text += "🚀 **Ready to find the next 100x?**"
    
    return help_text

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_ui_formatters():
    """Initialize the UI formatting system"""
    logger.info("🎨 FCB v2 UI Formatters initialized")
    logger.info("✨ Clean design matching FCB v1 style")

# Auto-initialize when module is imported
initialize_ui_formatters()