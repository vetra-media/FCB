print("Importing database...")
from database import (
    init_user_db, 
    get_user_balance, 
    spend_fcb_token, 
    add_fcb_tokens, 
    check_rate_limit_with_fcb
)
print("database imported")

print("Importing config...")
from config import (
    BOT_TOKEN, COINGECKO_API_KEY, COINGECKO_API, BROADCAST_CHAT_ID,
    RATE_LIMIT_SECONDS, FOMO_SCAN_INTERVAL, MAX_COINS_PER_PAGE, 
    TOP_N_TO_EXCLUDE, COIN_SYMBOL_OVERRIDES, STABLECOIN_SYMBOLS,
    FCB_STAR_PACKAGES, FOMO_CACHE, CACHE_REFRESH_INTERVAL,
    INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, HISTORY_LOG,
    validate_config
)
print("config imported")

print("Importing api_client...")
from api_client import (
    get_optimized_session, OptimizedRateLimiter, BatchProcessor,
    fetch_market_data_ultra_fast, fetch_ohlcv_data_ultra_fast,
    fetch_ticker_data_ultra_fast, fetch_coin_data_ultra_fast,
    get_coin_info_ultra_fast, fetch_ohlcv_data, fetch_from_coingecko,
    get_coin_info, fuzzy_find_coin, batch_processor, rate_limiter,
    cleanup_session
)
print("api_client imported")

print("Importing analysis...")
from analysis import (
    calculate_volume_spike_ultra_fast, analyze_momentum_trend_ultra_fast,
    analyze_exchange_distribution_ultra_fast, calculate_fomo_status_ultra_fast,
    analyze_exchange_distribution, analyze_momentum_trend,
    calculate_real_volume_spike, calculate_fomo_status
)
print("analysis imported")

print("Importing cache...")
from cache import init_ultra_fast_cache
print("cache imported")

print("Importing scanner...")
from scanner import periodic_fomo_scan
print("scanner imported")

print("Importing handlers...")
from handlers import setup_handlers
print("handlers imported")

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

# Load environment variables
load_dotenv()

print("=== STARTING SCRIPT ===")
print("Configuration importing...")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("Setting up logging...")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
print("Logging configured")  # <--- ADD THIS
logger = logging.getLogger(__name__)
print("Logger created")      # <--- ADD THIS


async def start_bot_only():
    """Start just the bot without background tasks first"""
    logger.info("🚀 Starting ULTRA-FAST FOMO Crypto Bot...")
    
    # Validate configuration
    try:
        validate_config()
        logger.info("✅ Configuration validated")
    except Exception as e:
        logger.error(f"❌ Config validation failed: {e}")
        return None
    
    # Initialize database  
    try:
        init_user_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        return None
    
    # Build and setup Telegram app
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        setup_handlers(app)
        logger.info("✅ Telegram app built and handlers setup")
    except Exception as e:
        logger.error(f"❌ Telegram setup failed: {e}")
        return None
    
    # Initialize and start bot
    try:
        await app.initialize()
        await app.start()
        logger.info("✅ Telegram bot started successfully")
        
        logger.info(f'✅ Bot is online! Chat ID: {BROADCAST_CHAT_ID}')
        logger.info(f"🔑 Using CoinGecko Pro API: {COINGECKO_API_KEY[:8]}...")
        
        return app
    except Exception as e:
        logger.error(f"❌ Bot start failed: {e}")
        return None

async def start_background_tasks(app):
    print("=== ENTERED start_background_tasks() ===")
    """Start background tasks after bot is confirmed working"""
    logger.info("🔄 Starting background tasks...")
    
    tasks = []
    
    try:
        print("About to start bot polling...")  # <-- ADD THIS
        # Start polling (this keeps the bot responsive)
        logger.info("🔄 Starting bot polling...")
        polling_task = asyncio.create_task(app.updater.start_polling())
        tasks.append(polling_task)
        logger.info("✅ Bot polling started")
        print("Bot polling started successfully")  # <-- ADD THIS
        
        # Small delay to let polling establish
        await asyncio.sleep(2)
        print("After polling delay")  # <-- ADD THIS
        
        print("About to start cache system...")  # <-- ADD THIS
        # Start cache system
        logger.info("🔄 Starting cache system...")
        cache_task = asyncio.create_task(init_ultra_fast_cache())
        tasks.append(cache_task)
        logger.info("✅ Cache task started")
        print("Cache task started successfully")  # <-- ADD THIS
        
        # Another small delay
        await asyncio.sleep(1)
        print("After cache delay")  # <-- ADD THIS
        
        print("About to start FOMO scanner...")  # <-- ADD THIS
        # Start FOMO scanner
        logger.info("🔄 Starting FOMO scanner...")
        scanner_task = asyncio.create_task(periodic_fomo_scan(app.bot))
        tasks.append(scanner_task)
        logger.info("✅ Scanner task started")
        print("Scanner task started successfully")  # <-- ADD THIS
        
        logger.info("🎯 All systems operational! Bot ready for commands.")
        print("All systems operational, returning tasks")  # <-- ADD THIS
        
        return tasks
        
    except Exception as e:
        print(f"Exception in start_background_tasks: {e}")  # <-- ADD THIS
        logger.error(f"❌ Background task startup failed: {e}")
        # Cancel any tasks that were started
        for task in tasks:
            if not task.done():
                task.cancel()
        return []

async def main():
    print("Entered main()")
    print("About to call start_bot_only()")
    app = await start_bot_only()
    print(f"Returned from start_bot_only(), app = {app}")
    print("Returned from start_bot_only()")
    if not app:
        print("No app, exiting main()")
        return

    print("About to call start_background_tasks()")
    tasks = await start_background_tasks(app)
    print("Returned from start_background_tasks()")
    if not tasks:
        print("No tasks, stopping app")
        await app.stop()
        return

    print("Running background tasks...")
    print("🎯 Bot is now running! Press Ctrl+C to stop.")
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Exception in main: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)