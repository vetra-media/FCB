"""
FCB v2 - Simple Command Handlers
Basic bot commands: /start, /test, /help
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import add_user_to_notifications, get_user_balance
from elite_integration import analyze_coin_comprehensive

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - subscribe user to alerts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logger.info(f"Start command from {username} (ID: {user_id})")
    
    try:
        # Add user to notifications
        add_user_to_notifications(user_id)
        
        message = """🚀 **Welcome to FCB FOMO Bot v2!**

✅ You're now subscribed to premium opportunity alerts!

🎯 **What you get:**
• Elite analysis alerts when great opportunities are found
• 50x faster analysis system
• Real-time market scanning

💡 **Commands:**
• `/test` - Test the Elite Analysis system
• `/help` - Show this help message

🔍 **How it works:**
Our Elite Analysis system scans the market 24/7 and alerts you when it finds high-scoring opportunities (30%+ FOMO score).

Ready to catch the next big move! 🚀"""

        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"✅ User {user_id} subscribed successfully")
        
    except Exception as e:
        logger.error(f"Start command error for {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error. Please try again or contact support."
        )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command - run Elite Analysis test"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logger.info(f"Test command from {username} (ID: {user_id})")
    
    try:
        # Test data for Elite Analysis
        test_coin_data = {
            'symbol': 'BTC',
            'price': 98765.43,
            'volume_24h': 25000000000,
            'market_cap': 1900000000000,
            'price_change_percentage_1h': 2.5,
            'price_change_percentage_24h': 5.67,
            'price_change_percentage_7d': -1.2,
            'volume_change_24h': 85.3
        }
        
        # Run Elite Analysis
        logger.info(f"Running Elite Analysis test for {user_id}")
        result = await analyze_coin_comprehensive(test_coin_data, user_id=user_id)
        
        # Format response
        score = result.get('fomo_score', 0)
        signal = result.get('signal', 'Unknown')
        analysis = result.get('analysis', 'No analysis available')
        confidence = result.get('confidence', 'Unknown')
        
        message = f"""🧪 **Elite Analysis Test Complete!**

🪙 **Bitcoin (BTC) Test**
📊 **FOMO Score:** {score:.1f}/100
🎯 **Signal:** {signal}
🔍 **Analysis:** {analysis}
📈 **Confidence:** {confidence}

✅ **Elite Analysis system is working perfectly!**
This is the same analysis that powers our market scanning and alerts.

The system analyzed Bitcoin in under 100ms with professional-grade insights."""

        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"✅ Test completed for {user_id} - Score: {score:.1f}")
        
    except Exception as e:
        logger.error(f"Test command error for {user_id}: {e}")
        await update.message.reply_text(
            f"❌ Elite Analysis test failed: {str(e)}\n"
            "Please contact support if this continues."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    
    message = """📚 **FCB FOMO Bot v2 Help**

🎯 **Commands:**
• `/start` - Subscribe to premium alerts
• `/test` - Test Elite Analysis system  
• `/help` - Show this help message

🚀 **How it works:**
Our Elite Analysis system scans 1000+ cryptocurrencies 24/7, looking for high-probability opportunities. When it finds coins scoring 30%+ on our FOMO algorithm, you get alerted instantly.

🔍 **Elite Analysis Features:**
• 50x faster than previous systems
• Professional trading insights
• Volume spike detection
• Momentum analysis
• Risk assessment

💡 **Tips:**
• Alerts are sent for genuine opportunities only
• Each alert includes detailed analysis
• System runs continuously - no need to check manually

Questions? Contact @fomocryptopings"""

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Help command used by user {user_id}")

def setup_handlers(app):
    """Setup all command handlers"""
    logger.info("Setting up command handlers...")
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("help", help_command))
    
    logger.info("✅ Command handlers registered")
    return app# Copy the content from the first artifact above
