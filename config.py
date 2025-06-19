"""
Configuration module for CFB (Crypto FOMO Bot)
Handles environment variables, API settings, and validation
✅ UPDATED: Complete Pro API integration with enhanced features
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import logging
import requests

# Dynamically load the correct .env file based on ENV_MODE
ENV_MODE = os.getenv('ENV_MODE', 'test')  # default to 'test' if not set
env_path = Path('.') / f'.env.{ENV_MODE}'
load_dotenv(dotenv_path=env_path)

prod_token = os.getenv('BOT_TOKEN')
test_token = os.getenv('TEST_BOT_TOKEN')

print(f"🌍 Loaded environment: {ENV_MODE} ({env_path})")
print("✅ Config summary:")
print(f"  • ENV_MODE: {ENV_MODE}")
print(f"  • TEST_MODE: {os.getenv('TEST_MODE')}")
print(f"  • BOT_TOKEN: {prod_token[:10] + '... (prod)'}" if prod_token else "  • BOT_TOKEN: Not set (prod)")
print(f"  • TEST_BOT_TOKEN: {test_token[:10] + '... (test)'}" if test_token else "  • TEST_BOT_TOKEN: Not set (test)")
print(f"  • BROADCAST_CHAT_ID: {os.getenv('BROADCAST_CHAT_ID')}")
print(f"  • CoinGecko API Key: {os.getenv('COINGECKO_API_KEY')[:8]}...")
print(f"  • SHORTIO_LINK_ID: {os.getenv('SHORTIO_LINK_ID')}")

# =============================================================================
# CORE CONFIGURATION
# =============================================================================

# Bot Configuration
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
BOT_TOKEN = os.getenv('TEST_BOT_TOKEN') if TEST_MODE else os.getenv('BOT_TOKEN')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')

# Chat IDs for different purposes
INTERACTIVE_CHAT_ID = None  # Will be set per user interaction
BROADCAST_CHAT_ID = os.getenv('BROADCAST_CHAT_ID')

# API Configuration
COINGECKO_API = "https://pro-api.coingecko.com/api/v3"

# NEW: Tracking link configuration
SHORTIO_LINK_ID = os.getenv('SHORTIO_LINK_ID', 'https://fomocryptopings.short.gy/coingeckosub+fomocryptopings')

# =============================================================================
# ✅ PRO API CONFIGURATION - ENHANCED INTEGRATION
# =============================================================================

# Pro API specific settings
COINGECKO_PRO_API_KEY = os.getenv('COINGECKO_API_KEY')  # Use your existing env var
COINGECKO_PRO_BASE_URL = COINGECKO_API  # Use your existing URL

# Pro API Rate Limits (much higher than free API)
PRO_API_RATE_LIMIT = 500  # calls per minute (vs 5-15 for free)
PRO_API_TIMEOUT = 15  # seconds
PRO_API_BATCH_SIZE = 50  # Higher batch sizes allowed

# =============================================================================
# RATE LIMITING CONFIGURATION - OPTIMIZED FOR PRO API
# =============================================================================

# OPTIMIZED RATE LIMITING FOR 500 CALLS/MINUTE
RATE_LIMIT_SECONDS = 1  # Reduced from 5 to 1 second
MAX_CONCURRENT_REQUESTS = 50  # Increased from 20 to 50
BATCH_SIZE = 25  # Optimized batch size
COINGECKO_DELAY = 0.12  # 500/min = 0.12s minimum interval

# =============================================================================
# FOMO SCANNING CONFIGURATION - PRO API OPTIMIZED
# =============================================================================

# FOMO scanning configuration - OPTIMIZED FOR PRO API
FOMO_SCAN_INTERVAL = 2 * 3600  # Reduced to 2 hours for more frequent alerts
MAX_COINS_PER_PAGE = 250  # Pro API allows up to 250 per page
TOP_N_TO_EXCLUDE = 15

# =============================================================================
# COIN AND MARKET CONFIGURATION
# =============================================================================

COIN_SYMBOL_OVERRIDES = {
    'btc': 'bitcoin', 'bitcoin': 'bitcoin', 'eth': 'ethereum', 'ethereum': 'ethereum',
    'pepe': 'pepe', 'pepecoin': 'pepe', 'bonk': 'bonk', 'doge': 'dogecoin', 'dogecoin': 'dogecoin',
}

STABLECOIN_SYMBOLS = {
    "usdt", "usdc", "dai", "tusd", "usdp", "gusd", "alusd", "eurt", "busd", "usdd",
    "fdusd", "usdn", "mim", "usde", "frax", "sai", "lusd", "susd", "hbusd", "vai",
    "eurc", "ageur", "eurs", "musd", "cusd", "xaut", "xusd", "paxg", "bitusd",
    "usdx", "usds", "usdsb", "celo", "fei", "usdk", "ousd", "usdq",
    "husd", "bai", "xsgd", "usdtez", "usd+", "usyc", "usdl", "pusd"
}

# =============================================================================
# FCB TOKEN CONFIGURATION - ENHANCED WITH PRO API POSITIONING
# =============================================================================

# FCB Token Configuration
FCB_TOKEN_CONTRACT = "0x..."  # Will add real contract address
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# ✅ ENHANCED FCB Star Packages with Pro API positioning
FCB_STAR_PACKAGES = {
    'starter': {
        'title': '🪙 Premium Tokens (Starter)',
        'description': '10 Premium Scans - Each worth 10 stars of market analysis',
        'stars': 100,
        'tokens': 10,
        'value_prop': '🎯 Perfect for: Testing premium features\n💡 Each scan processes $50,000+ worth of real-time data'
    },
    'premium': {
        'title': '🔥 Premium Tokens (Most Popular)',
        'description': '25 Premium Scans - Professional-grade analysis per scan',
        'stars': 250,
        'tokens': 25,
        'value_prop': '⚡ Perfect for: Active crypto discovery\n🏆 LEGENDARY opportunities have 1.3x better odds\n💎 Institutional-grade FOMO analysis'
    },
    'pro': {
        'title': '⭐ Premium Tokens (Pro)',
        'description': '50 Premium Scans - Advanced market intelligence',
        'stars': 500,
        'tokens': 50,
        'value_prop': '🚀 Perfect for: Serious traders\n👑 Premium user bonuses active\n📊 15+ market indicators per scan'
    },
    'elite': {
        'title': '👑 Premium Tokens (Elite)',
        'description': '100 Premium Scans - Whale-tier analysis power',
        'stars': 1000,
        'tokens': 100,
        'value_prop': '💰 Perfect for: Crypto institutions\n🎰 Maximum psychology bonuses\n⚡ Priority access to breakthrough opportunities'
    }
}

# =============================================================================
# ✅ ENHANCED CACHE CONFIGURATION FOR PRO API
# =============================================================================

# Enhanced cache with Pro API tracking
FOMO_CACHE = {
    'coins': [],
    'last_update': None,
    'current_index': 0,
    'pro_api_active': True,  # NEW: Track Pro API status
    'last_pro_fetch': 0,     # NEW: Track last Pro API call
    'fetch_attempts': 0,     # NEW: Track failed attempts
    'fallback_mode': False   # NEW: Track if using fallback
}

# Reduce cache intervals since Pro API updates faster
CACHE_BACK_INTERVAL = 120  # 2 minutes (reduced from 180)
PRO_API_CACHE_TTL = 60     # 1 minute cache for Pro API data

# =============================================================================
# ✅ PRO API ENHANCED RESPONSE MESSAGES
# =============================================================================

# Original instant responses
INSTANT_RESPONSES = [
    "🎯 BOOM! Found something...",
    "🚀 Scanning... signals detected!",
    "⚡ Market moving... analyzing...",
    "🔥 Volume spike detected!",
    "💎 Hidden gem incoming...",
    "🎪 Opportunity detected!",
    "🌟 FOMO alert building..."
]

# NEW: Pro API specific loading messages
PRO_API_LOADING_MESSAGES = [
    "🔑 Pro API scanning...",
    "⚡ 500 calls/min power...",
    "💎 Institutional data loading...",
    "🏆 Premium analysis running...",
    "👑 Whale-tier scanning...",
    "🎯 Professional signals...",
    "🚀 Advanced algorithms working...",
    "💰 High-value opportunities..."
]

# NEW: Enhanced instant responses for Pro API
INSTANT_RESPONSES_PRO = [
    "🔑 Pro API detected signals...",
    "⚡ 500 calls/min scanning power...",
    "💎 Institutional-grade analysis...",
    "🏆 Premium data processing...",
    "👑 Professional signals incoming...",
    "🎯 Advanced FOMO algorithms active...",
    "🚀 Breakthrough opportunity hunt...",
    "💰 Whale-tier analysis running..."
]

# Original spin responses
INSTANT_SPIN_RESPONSES = [
    "🎰 Spinning the FOMO wheel...",
    "🎲 Rolling for moon shots...",
    "💎 Hunting for hidden gems...",
    "🚀 Searching for rockets...",
    "⚡ Scanning for lightning...",
    "🔥 Detecting hot coins...",
    "🎯 Targeting opportunities...",
    "💰 Seeking gold mines...",
    "🌟 Finding shooting stars...",
    "🎪 Discovering magic..."
]

# =============================================================================
# FILE PATHS
# =============================================================================

HISTORY_LOG = "fomo_variety_history.csv"

# =============================================================================
# HELPER FUNCTIONS FOR TRACKING LINKS
# =============================================================================

def get_buy_coin_url(coin_data):
    """
    Generate tracking URL for BUY COIN button
    Uses SHORTIO_LINK_ID as base tracking link
    """
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
# ✅ ENHANCED VALIDATION WITH PRO API CHECKS
# =============================================================================

def validate_pro_api_config():
    """Enhanced Pro API specific validation"""
    
    errors = []
    warnings = []
    
    # Check Pro API key format
    if COINGECKO_PRO_API_KEY:
        if not COINGECKO_PRO_API_KEY.startswith('CG-'):
            warnings.append("Pro API key should start with 'CG-'")
        
        if len(COINGECKO_PRO_API_KEY) < 20:
            errors.append("Pro API key appears too short")
    
    # Check Pro API URL
    if not COINGECKO_PRO_BASE_URL.startswith('https://pro-api.coingecko.com'):
        errors.append("Pro API URL should use pro-api.coingecko.com")
    
    # Test Pro API connectivity with your key
    if COINGECKO_PRO_API_KEY:
        try:
            test_url = f"{COINGECKO_PRO_BASE_URL}/ping"
            test_params = {'x_cg_pro_api_key': COINGECKO_PRO_API_KEY}
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('gecko_says') == '(V3) To the Moon!':
                    logging.info("✅ CoinGecko Pro API: Authentication successful!")
                    logging.info(f"🔑 Pro API: Using key {COINGECKO_PRO_API_KEY[:8]}...")
                    
                    # Test rate limit info
                    remaining = response.headers.get('x-ratelimit-remaining')
                    if remaining:
                        logging.info(f"🔑 Pro API: Rate limit remaining: {remaining}")
                else:
                    warnings.append("Pro API ping response format unexpected")
            
            elif response.status_code == 401:
                errors.append(f"Pro API key invalid: {COINGECKO_PRO_API_KEY[:8]}...")
            
            elif response.status_code == 403:
                errors.append("Pro API key valid but access denied - check plan status")
            
            elif response.status_code == 429:
                logging.info("✅ Pro API key works (hit rate limit during test)")
            
            else:
                warnings.append(f"Pro API test returned status {response.status_code}")
        
        except Exception as e:
            warnings.append(f"Cannot test Pro API connectivity: {e}")
    
    return errors, warnings

def validate_config():
    """✅ ENHANCED validation with Pro API checks"""
    
    if TEST_MODE:
        logging.info("🔧 Running in TEST_MODE - using test bot and test chat ID")

    errors = []
    warnings = []

    # Critical checks
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is missing - bot cannot start")
    elif len(BOT_TOKEN) < 40:
        errors.append("BOT_TOKEN appears invalid (too short)")
    
    if not COINGECKO_API_KEY:
        errors.append("COINGECKO_API_KEY is missing - all coin lookups will fail")
    elif not COINGECKO_API_KEY.startswith('CG-'):
        warnings.append("COINGECKO_API_KEY should start with 'CG-'")
    
    if not BROADCAST_CHAT_ID:
        warnings.append("BROADCAST_CHAT_ID is missing - no automatic alerts will be sent")

    if not SHORTIO_LINK_ID:
        warnings.append("SHORTIO_LINK_ID is missing - BUY COIN buttons will use fallback URLs")
    elif not SHORTIO_LINK_ID.startswith('http'):
        warnings.append("SHORTIO_LINK_ID should be a valid URL")
    
    # ✅ NEW: Add Pro API validation
    pro_errors, pro_warnings = validate_pro_api_config()
    errors.extend(pro_errors)
    warnings.extend(pro_warnings)
    
    # Enhanced CoinGecko API test with Pro API features
    if COINGECKO_API_KEY:
        try:
            test_url = f"{COINGECKO_API}/ping"
            test_params = {'x_cg_pro_api_key': COINGECKO_API_KEY}
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                logging.info("✅ CoinGecko Pro API connection successful")
                
                # Check if we have rate limit headers (Pro API feature)
                rate_remaining = response.headers.get('x-ratelimit-remaining')
                rate_limit = response.headers.get('x-ratelimit-limit')
                
                if rate_remaining and rate_limit:
                    logging.info(f"🔑 Pro API Rate Limit: {rate_remaining}/{rate_limit} remaining")
                    
                    # Update cache with Pro API status
                    FOMO_CACHE['pro_api_active'] = True
                    FOMO_CACHE['last_pro_fetch'] = 0  # Reset fetch tracking
                else:
                    logging.info("✅ Pro API connected (no rate limit headers in ping)")
                
            elif response.status_code == 401:
                errors.append("COINGECKO_API_KEY is invalid - authentication failed")
            elif response.status_code == 429:
                logging.info("✅ CoinGecko Pro API key works (rate limit hit during test)")
            elif response.status_code == 403:
                errors.append("COINGECKO_API_KEY is valid but plan doesn't allow Pro API access")
            else:
                warnings.append(f"CoinGecko API returned unexpected status {response.status_code}")
                
        except requests.exceptions.Timeout:
            warnings.append("CoinGecko API timeout - network might be slow")
        except requests.exceptions.ConnectionError:
            warnings.append("Cannot connect to CoinGecko API - check internet connection")
        except Exception as e:
            warnings.append(f"Cannot test CoinGecko API: {e}")
    
    # Check rate limiting configuration
    if RATE_LIMIT_SECONDS < 1:
        warnings.append("RATE_LIMIT_SECONDS is very low - may cause API issues")
    if FOMO_SCAN_INTERVAL < 3600:
        warnings.append("FOMO_SCAN_INTERVAL is less than 1 hour - may hit API limits")
    
    # Log results with Pro API context
    if errors:
        logging.error("❌ CRITICAL CONFIGURATION ERRORS:")
        for error in errors:
            logging.error(f"  - {error}")
    
    if warnings:
        logging.warning("⚠️ Configuration warnings:")
        for warning in warnings:
            logging.warning(f"  - {warning}")
    
    if not errors and not warnings:
        logging.info("✅ Configuration validation passed - Pro API ready!")
        logging.info(f"🔑 Pro API Features: 500+ calls/min, 30s updates, enhanced data")
    
    # Stop if critical errors
    if errors:
        raise ValueError(f"Critical configuration errors found: {', '.join(errors)}")
    
    return True

# =============================================================================
# ✅ PRO API UTILITY FUNCTIONS
# =============================================================================

def get_pro_api_status():
    """Get current Pro API status for debugging"""
    
    return {
        'api_key': COINGECKO_PRO_API_KEY[:8] + '...' if COINGECKO_PRO_API_KEY else 'Not set',
        'base_url': COINGECKO_PRO_BASE_URL,
        'rate_limit': PRO_API_RATE_LIMIT,
        'timeout': PRO_API_TIMEOUT,
        'cache_ttl': PRO_API_CACHE_TTL,
        'cache_active': FOMO_CACHE.get('pro_api_active', False),
        'fallback_mode': FOMO_CACHE.get('fallback_mode', False)
    }

def log_pro_api_config():
    """Log Pro API configuration for startup verification"""
    
    status = get_pro_api_status()
    
    logging.info("🔑 Pro API Configuration:")
    logging.info(f"  • API Key: {status['api_key']}")
    logging.info(f"  • Base URL: {status['base_url']}")
    logging.info(f"  • Rate Limit: {status['rate_limit']} calls/min")
    logging.info(f"  • Timeout: {status['timeout']}s")
    logging.info(f"  • Cache TTL: {status['cache_ttl']}s")
    logging.info(f"  • Pro API Active: {status['cache_active']}")
    logging.info(f"  • Fallback Mode: {status['fallback_mode']}")

def get_pro_loading_message():
    """Get a random Pro API loading message"""
    import random
    return random.choice(PRO_API_LOADING_MESSAGES)

def get_pro_instant_response():
    """Get a random Pro API instant response"""
    import random
    return random.choice(INSTANT_RESPONSES_PRO)

# =============================================================================
# STARTUP CONFIGURATION LOGGING
# =============================================================================

def log_startup_config():
    """Log complete configuration for startup verification"""
    
    logging.info("🚀 CRYPTO FOMO BOT - STARTUP CONFIGURATION")
    logging.info("=" * 50)
    
    # Core config
    logging.info(f"📱 Bot Mode: {'TEST' if TEST_MODE else 'PRODUCTION'}")
    logging.info(f"🔑 Bot Token: {BOT_TOKEN[:10]}... ({'test' if TEST_MODE else 'prod'})")
    logging.info(f"📢 Broadcast Chat: {BROADCAST_CHAT_ID}")
    
    # Pro API config
    log_pro_api_config()
    
    # Rate limiting
    logging.info(f"⚡ Rate Limiting:")
    logging.info(f"  • Rate Limit: {RATE_LIMIT_SECONDS}s between requests")
    logging.info(f"  • Max Concurrent: {MAX_CONCURRENT_REQUESTS}")
    logging.info(f"  • CoinGecko Delay: {COINGECKO_DELAY}s")
    
    # Cache config
    logging.info(f"💾 Cache Configuration:")
    logging.info(f"  • Cache Interval: {CACHE_BACK_INTERVAL}s")
    logging.info(f"  • Pro API TTL: {PRO_API_CACHE_TTL}s")
    logging.info(f"  • Max Coins Per Page: {MAX_COINS_PER_PAGE}")
    
    # FOMO scanning
    logging.info(f"🎯 FOMO Scanning:")
    logging.info(f"  • Scan Interval: {FOMO_SCAN_INTERVAL/3600:.1f} hours")
    logging.info(f"  • Top N Exclude: {TOP_N_TO_EXCLUDE}")
    
    # Token economics
    logging.info(f"🪙 Token Economics:")
    logging.info(f"  • Free Queries/Day: {FREE_QUERIES_PER_DAY}")
    logging.info(f"  • New User Bonus: {NEW_USER_BONUS}")
    logging.info(f"  • Star Packages: {len(FCB_STAR_PACKAGES)} tiers")
    
    logging.info("=" * 50)
    logging.info("✅ Configuration loaded successfully!")

# Call during startup if run directly
if __name__ == "__main__":
    validate_config()
    log_startup_config()