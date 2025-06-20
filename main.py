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
    FCB_STAR_PACKAGES, FOMO_CACHE, CACHE_BACK_INTERVAL,
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
from scanner import periodic_fomo_scan, send_weekly_winners_update
print("scanner imported")

print("Importing handlers...")
from handlers import setup_handlers
print("handlers imported")

import os
import logging
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import aiohttp
import asyncio
from telegram import Bot

async def ping():
    bot = Bot("YOUR_BOT_TOKEN")
    me = await bot.get_me()
    print(me)

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
    
async def start_bot_only():
    """Start just the bot without background tasks first"""
    print("🚀 SIMPLE TEST: start_bot_only() function STARTED!")
    print("🔍 DEBUG: About to call logger.info...")
    logger.info("🚀 Starting ULTRA-FAST FOMO Crypto Bot...")
    print("🔍 DEBUG: Logger.info called successfully")
    
    # Validate configuration
    print("🔍 DEBUG: About to validate config...")
    try:
        validate_config()
        print("🔍 DEBUG: validate_config() completed")
        logger.info("✅ Configuration validated")
        print("🔍 DEBUG: Config validation logged")
    except Exception as e:
        print(f"🔍 DEBUG: Config validation failed: {e}")
        logger.error(f"❌ Config validation failed: {e}")
        return None
    
    # Initialize database  
    print("🔍 DEBUG: About to init database...")
    try:
        init_user_db()
        print("🔍 DEBUG: init_user_db() completed")
        logger.info("✅ Database initialized")
        print("🔍 DEBUG: Database init logged")
    except Exception as e:
        print(f"🔍 DEBUG: Database init failed: {e}")
        logger.error(f"❌ Database init failed: {e}")
        return None
    
    # Build and setup Telegram app
    print("🔍 DEBUG: About to build Telegram app...")
    try:
        token = os.getenv("TEST_BOT_TOKEN") if os.getenv("TEST_MODE") == "True" else BOT_TOKEN
        print(f"🔍 DEBUG: Got token: {token[:20]}...")
        logger.info(f"🔑 Using token: {token[:20]}...")
        
        app = ApplicationBuilder().token(token).build()
        print("🔍 DEBUG: ApplicationBuilder completed")
        logger.info("✅ Telegram app built")
        
        print("🔍 DEBUG: About to call setup_handlers...")
        setup_handlers(app)
        print("🔍 DEBUG: setup_handlers completed")
        logger.info("✅ setup_handlers completed")
        
        logger.info("✅ Telegram app built and handlers setup")
        
    except Exception as e:
        print(f"🔍 DEBUG: Telegram setup failed: {e}")
        logger.error(f"❌ Telegram setup failed: {e}")
        return None
    
    # Initialize and start bot
    print("🔍 DEBUG: About to initialize and start bot...")
    try:
        await app.initialize()
        print("🔍 DEBUG: app.initialize() completed")
        await app.start()
        print("🔍 DEBUG: app.start() completed")
        logger.info("✅ Telegram bot started successfully")
        
        logger.info(f'✅ Bot is online! Chat ID: {BROADCAST_CHAT_ID}')
        logger.info(f"🔑 Using CoinGecko Pro API: {COINGECKO_API_KEY[:8]}...")
        
        print("🔍 DEBUG: About to return app...")
        return app
    except Exception as e:
        print(f"🔍 DEBUG: Bot start failed: {e}")
        logger.error(f"❌ Bot start failed: {e}")
        return None
        
async def ping_render_service():
    """Keep the service active by making an external request"""
    try:
        # Just ping a reliable external service to generate activity
        async with aiohttp.ClientSession() as session:
            async with session.get("https://httpbin.org/status/200", timeout=10) as response:
                if response.status == 200:
                    logger.info("✅ Keep-alive ping successful")
                else:
                    logger.warning(f"⚠️ Keep-alive ping returned status {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Keep-alive ping failed: {e}")
        # Don't raise the exception - just log it so the scheduler continues

async def start_background_tasks(app):
    print("=== ENTERED start_background_tasks() ===")
    """Start background tasks after bot is confirmed working"""
    logger.info("🔄 Starting background tasks...")
    
    tasks = []
    scheduler = None
    
    try:
        print("About to start bot polling...")
        # Start polling (this keeps the bot responsive)
        logger.info("🔄 Starting bot polling...")
        polling_task = asyncio.create_task(app.updater.start_polling())
        tasks.append(polling_task)
        logger.info("✅ Bot polling started")
        print("Bot polling started successfully")
        
        # Small delay to let polling establish
        await asyncio.sleep(2)
        print("After polling delay")
        
        print("About to start cache system...")
        # Start cache system
        logger.info("🔄 Starting cache system...")
        cache_task = asyncio.create_task(init_ultra_fast_cache())
        tasks.append(cache_task)
        logger.info("✅ Cache task started")
        print("Cache task started successfully")
        
        # Another small delay
        await asyncio.sleep(1)
        print("After cache delay")
        
        # Start scheduled FOMO broadcasts every 4 hours with weekly winners
        print("About to start scheduled FOMO alerts...")
        logger.info("🕒 Setting up scheduled FOMO alerts (every 4 hours)...")
        scheduler = AsyncIOScheduler(timezone=timezone("Asia/Kolkata"))
        
        # FOMO alerts every 4 hours (6 per day max)
        scheduler.add_job(
            periodic_fomo_scan,
            'interval',
            hours=4,
            args=[app.bot]
        )
        
        # Weekly winners update daily at 10 AM IST
        scheduler.add_job(
            send_weekly_winners_update,
            'cron',
            hour=10,
            args=[app.bot]
        )
        
        # Add ping job to keep Render service awake
        scheduler.add_job(
            ping_render_service,
            'interval', 
            minutes=14  # Ping every 14 minutes to keep service awake
        )

        scheduler.start()
        logger.info("✅ Scheduler started for 6am, 2pm, and 10pm IST")
        logger.info("✅ Ping service started (every 14 minutes)")

        # Run initial FOMO scan on startup
        try:
            logger.info("🔄 Running initial FOMO scan on startup...")
            await periodic_fomo_scan(app.bot)
            logger.info("✅ Initial FOMO scan completed")
        except Exception as e:
            logger.error(f"❌ Initial FOMO scan failed: {e}")

        logger.info("🎯 All systems operational! Bot ready for commands.")
        print("All systems operational, returning tasks")
        
        return tasks, scheduler  # Return scheduler so it can be managed
        
    except Exception as e:
        print(f"Exception in start_background_tasks: {e}")
        logger.error(f"❌ Background task startup failed: {e}")
        
        # Clean up scheduler if it was created
        if scheduler:
            scheduler.shutdown()
        
        # Cancel any tasks that were started
        for task in tasks:
            if not task.done():
                task.cancel()
        return [], None

async def main():
    print("Entered main()")
    print("About to call start_bot_only()")
    app = await start_bot_only()
    print(f"Returned from start_bot_only(), app = {app}")
    if not app:
        print("No app, exiting main()")
        return

    print("About to call start_background_tasks()")
    tasks, scheduler = await start_background_tasks(app)
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
    finally:
        # Clean shutdown
        if scheduler:
            scheduler.shutdown()
        await app.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)