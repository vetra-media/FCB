import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

print("=== STARTING SCRIPT ===")
print("Environment variables loaded...")

# Setup basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_import(module_name, import_statement):
    """Test importing a module and report success/failure"""
    try:
        print(f"Importing {module_name}...")
        exec(import_statement)
        print(f"✅ {module_name} imported successfully")
        return True
    except Exception as e:
        print(f"❌ {module_name} failed to import: {e}")
        return False

def main():
    """Diagnostic main to test imports one by one"""
    print("Starting diagnostic import testing...")
    
    # Test imports one by one
    imports_to_test = [
        ("database", """
from database import (
    init_user_db, 
    get_user_balance, 
    spend_fcb_token, 
    add_fcb_tokens, 
    check_rate_limit_with_fcb
)"""),
        
        ("config", """
from config import (
    BOT_TOKEN, COINGECKO_API_KEY, COINGECKO_API, BROADCAST_CHAT_ID,
    RATE_LIMIT_SECONDS, FOMO_SCAN_INTERVAL, MAX_COINS_PER_PAGE, 
    TOP_N_TO_EXCLUDE, COIN_SYMBOL_OVERRIDES, STABLECOIN_SYMBOLS,
    FCB_STAR_PACKAGES, FOMO_CACHE, CACHE_REFRESH_INTERVAL,
    INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, HISTORY_LOG,
    validate_config
)"""),
        
        ("api_client", """
from api_client import (
    get_optimized_session, OptimizedRateLimiter, BatchProcessor,
    fetch_market_data_ultra_fast, fetch_ohlcv_data_ultra_fast,
    fetch_ticker_data_ultra_fast, fetch_coin_data_ultra_fast,
    get_coin_info_ultra_fast, fetch_ohlcv_data, fetch_from_coingecko,
    get_coin_info, fuzzy_find_coin, batch_processor, rate_limiter,
    cleanup_session
)"""),
        
        ("analysis", """
from analysis import (
    calculate_volume_spike_ultra_fast, analyze_momentum_trend_ultra_fast,
    analyze_exchange_distribution_ultra_fast, calculate_fomo_status_ultra_fast,
    analyze_exchange_distribution, analyze_momentum_trend,
    calculate_real_volume_spike, calculate_fomo_status
)"""),
        
        ("cache", "from cache import init_ultra_fast_cache"),
        
        ("scanner", "from scanner import periodic_fomo_scan"),
        
        ("handlers", "from handlers import setup_handlers"),
        
        ("telegram", "from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters")
    ]
    
    failed_imports = []
    
    for module_name, import_statement in imports_to_test:
        success = test_import(module_name, import_statement)
        if not success:
            failed_imports.append(module_name)
        
        # Add a small delay to see progress
        import time
        time.sleep(0.5)
    
    print("\n=== IMPORT TESTING COMPLETE ===")
    
    if failed_imports:
        print(f"❌ Failed imports: {', '.join(failed_imports)}")
        print("Fix these modules before running the full bot.")
    else:
        print("✅ All imports successful!")
        print("The hang is likely happening inside one of the modules during import.")
        print("Check for:")
        print("  - API calls during import")
        print("  - Blocking database connections")
        print("  - Infinite loops in module initialization")
        print("  - Missing environment variables")
    
    # Test basic functionality
    print("\n=== TESTING BASIC FUNCTIONALITY ===")
    
    try:
        # Test that we can access config values
        exec("print(f'Bot token configured: {BOT_TOKEN[:10]}...')")
        print("✅ Config access works")
    except Exception as e:
        print(f"❌ Config access failed: {e}")
    
    try:
        # Test database init
        exec("init_user_db()")
        print("✅ Database initialization works")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

if __name__ == '__main__':
    main()