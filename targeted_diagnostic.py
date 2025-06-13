import os
import logging
import asyncio
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

print("=== STARTING SCRIPT ===")
print("Configuration importing...")

# Setup logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def timed_import(description, import_func):
    """Time how long an import takes and detect hangs"""
    print(f"⏱️  Starting: {description}")
    start_time = time.time()
    
    try:
        import_func()
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ Completed: {description} ({duration:.2f}s)")
        return True
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Failed: {description} ({duration:.2f}s) - {e}")
        return False

# Test the exact import pattern from main.py
print("\n=== TESTING EXACT IMPORT PATTERN ===")

def import_database():
    from database import (
        init_user_db, 
        get_user_balance, 
        spend_fcb_token, 
        add_fcb_tokens, 
        check_rate_limit_with_fcb
    )
    globals().update(locals())

def import_config():
    from config import (
        BOT_TOKEN, COINGECKO_API_KEY, COINGECKO_API, BROADCAST_CHAT_ID,
        RATE_LIMIT_SECONDS, FOMO_SCAN_INTERVAL, MAX_COINS_PER_PAGE, 
        TOP_N_TO_EXCLUDE, COIN_SYMBOL_OVERRIDES, STABLECOIN_SYMBOLS,
        FCB_STAR_PACKAGES, FOMO_CACHE, CACHE_REFRESH_INTERVAL,
        INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, HISTORY_LOG,
        validate_config
    )
    globals().update(locals())

def import_api_client():
    from api_client import (
        get_optimized_session, OptimizedRateLimiter, BatchProcessor,
        fetch_market_data_ultra_fast, fetch_ohlcv_data_ultra_fast,
        fetch_ticker_data_ultra_fast, fetch_coin_data_ultra_fast,
        get_coin_info_ultra_fast, fetch_ohlcv_data, fetch_from_coingecko,
        get_coin_info, fuzzy_find_coin, batch_processor, rate_limiter,
        cleanup_session
    )
    globals().update(locals())

def import_analysis():
    from analysis import (
        calculate_volume_spike_ultra_fast, analyze_momentum_trend_ultra_fast,
        analyze_exchange_distribution_ultra_fast, calculate_fomo_status_ultra_fast,
        analyze_exchange_distribution, analyze_momentum_trend,
        calculate_real_volume_spike, calculate_fomo_status
    )
    globals().update(locals())

def import_cache():
    from cache import init_ultra_fast_cache
    globals().update(locals())

def import_scanner():
    from scanner import periodic_fomo_scan
    globals().update(locals())

def import_handlers():
    from handlers import setup_handlers
    globals().update(locals())

def import_telegram():
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
    globals().update(locals())

# Test each import with timing
imports_to_test = [
    ("Database imports", import_database),
    ("Config imports", import_config),
    ("API Client imports", import_api_client), 
    ("Analysis imports", import_analysis),
    ("Cache imports", import_cache),
    ("Scanner imports", import_scanner),
    ("Handlers imports", import_handlers),
    ("Telegram imports", import_telegram),
]

print("Testing imports in exact order from main.py...")
print("⚠️  If this hangs, press Ctrl+C and note which import was running")

failed_imports = []
for description, import_func in imports_to_test:
    success = timed_import(description, import_func)
    if not success:
        failed_imports.append(description)
    
    # Small delay to see each step
    time.sleep(0.2)

print("\n=== TESTING COMPLETE ===")

if failed_imports:
    print(f"❌ Failed imports: {', '.join(failed_imports)}")
else:
    print("✅ All imports completed successfully!")
    
    # Now test the actual main function logic
    print("\n=== TESTING MAIN FUNCTION LOGIC ===")
    
    try:
        print("Testing validate_config()...")
        validate_config()
        print("✅ Config validation successful")
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
    
    try:
        print("Testing init_user_db()...")
        init_user_db()
        print("✅ Database init successful")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
    
    try:
        print("Testing Telegram app creation...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        print("✅ Telegram app creation successful")
    except Exception as e:
        print(f"❌ Telegram app creation failed: {e}")

print("\n🎯 If this diagnostic completes but main.py still hangs,")
print("   the issue is likely in the async task coordination.")

if __name__ == '__main__':
    pass