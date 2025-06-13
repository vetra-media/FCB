print("Testing main.py imports one by one...")

print("1. Basic imports...")
import os
import logging
import asyncio
from dotenv import load_dotenv
print("✅ Basic imports OK")

print("2. Database imports...")
from database import (
    init_user_db, 
    get_user_balance, 
    spend_fcb_token, 
    add_fcb_tokens, 
    check_rate_limit_with_fcb
)
print("✅ Database imports OK")

print("3. Config imports...")
from config import (
    BOT_TOKEN, COINGECKO_API_KEY, COINGECKO_API, BROADCAST_CHAT_ID,
    RATE_LIMIT_SECONDS, FOMO_SCAN_INTERVAL, MAX_COINS_PER_PAGE, 
    TOP_N_TO_EXCLUDE, COIN_SYMBOL_OVERRIDES, STABLECOIN_SYMBOLS,
    FCB_STAR_PACKAGES, FOMO_CACHE, CACHE_REFRESH_INTERVAL,
    INSTANT_RESPONSES, INSTANT_SPIN_RESPONSES, HISTORY_LOG,
    validate_config
)
print("✅ Config imports OK")

print("4. API client imports...")
from api_client import (
    get_optimized_session, OptimizedRateLimiter, BatchProcessor,
    fetch_market_data_ultra_fast, fetch_ohlcv_data_ultra_fast,
    fetch_ticker_data_ultra_fast, fetch_coin_data_ultra_fast,
    get_coin_info_ultra_fast, fetch_ohlcv_data, fetch_from_coingecko,
    get_coin_info, fuzzy_find_coin, batch_processor, rate_limiter,
    cleanup_session
)
print("✅ API client imports OK")

print("5. Analysis imports...")
from analysis import (
    calculate_volume_spike_ultra_fast, analyze_momentum_trend_ultra_fast,
    analyze_exchange_distribution_ultra_fast, calculate_fomo_status_ultra_fast,
    analyze_exchange_distribution, analyze_momentum_trend,
    calculate_real_volume_spike, calculate_fomo_status
)
print("✅ Analysis imports OK")

print("6. Cache imports...")
from cache import init_ultra_fast_cache
print("✅ Cache imports OK")

print("7. Scanner imports...")
from scanner import periodic_fomo_scan
print("✅ Scanner imports OK")

print("8. Handlers imports...")
from handlers import setup_handlers
print("✅ Handlers imports OK")

print("9. Telegram imports...")
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
print("✅ Telegram imports OK")

print("All main.py imports successful!")