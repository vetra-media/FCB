"""
Configuration module for CFB (Crypto FOMO Bot)
Handles environment variables, API settings, and validation
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
print(f"  • BROADCAST_CHAT_ID: {os.getenv('TEST_CHAT_ID') if os.getenv('TEST_MODE') == 'True' else os.getenv('CHAT_ID')}")
print(f"  • CoinGecko API Key: {os.getenv('COINGECKO_API_KEY')[:8]}...")

# =============================================================================
# CORE CONFIGURATION
# =============================================================================

# Bot Configuration
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
BOT_TOKEN = os.getenv('TEST_BOT_TOKEN') if TEST_MODE else os.getenv('BOT_TOKEN')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')

# Chat IDs for different purposes
INTERACTIVE_CHAT_ID = None  # Will be set per user interaction
BROADCAST_CHAT_ID = os.getenv('TEST_CHAT_ID') if TEST_MODE else os.getenv('CHAT_ID')

# API Configuration
COINGECKO_API = "https://pro-api.coingecko.com/api/v3"

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

# OPTIMIZED RATE LIMITING FOR 500 CALLS/MINUTE
RATE_LIMIT_SECONDS = 1  # Reduced from 5 to 1 second
MAX_CONCURRENT_REQUESTS = 50  # Increased from 20 to 50
BATCH_SIZE = 25  # Optimized batch size
COINGECKO_DELAY = 0.12  # 500/min = 0.12s minimum interval

# =============================================================================
# FOMO SCANNING CONFIGURATION
# =============================================================================

# FOMO scanning configuration - OPTIMIZED FOR PRO API
FOMO_SCAN_INTERVAL = 2 * 3600  # Reduced to 2 hours for more frequent alerts
MAX_COINS_PER_PAGE = 250
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
# FCB TOKEN CONFIGURATION
# =============================================================================

# FCB Token Configuration
FCB_TOKEN_CONTRACT = "0x..."  # Will add real contract address
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# FCB Star Packages
FCB_STAR_PACKAGES = {
    'starter': {
        'tokens': 100, 
        'stars': 100,  # 1:1 ratio
        'title': '100 FCB Tokens', 
        'description': 'Starter package - 100 scans'
    },
    'premium': {
        'tokens': 250, 
        'stars': 250,  # 1:1 ratio
        'title': '250 FCB Tokens', 
        'description': 'Premium package - 250 scans'
    },
    'pro': {
        'tokens': 500, 
        'stars': 500,  # 1:1 ratio
        'title': '500 FCB Tokens', 
        'description': 'Pro package - 500 scans'
    },
    'elite': {
        'tokens': 1000, 
        'stars': 1000,  # 1:1 ratio
        'title': '1000 FCB Tokens', 
        'description': 'Elite package - 1000 scans'
    }
}

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Global cache for instant results
FOMO_CACHE = {
    'coins': [],
    'last_update': None,
    'current_index': 0
}

CACHE_REFRESH_INTERVAL = 180  # Reduced to 3 minutes for fresher data

# =============================================================================
# RESPONSE MESSAGES
# =============================================================================

INSTANT_RESPONSES = [
    "🎯 BOOM! Found something...",
    "🚀 Scanning... signals detected!",
    "⚡ Market moving... analyzing...",
    "🔥 Volume spike detected!",
    "💎 Hidden gem incoming...",
    "🎪 Opportunity detected!",
    "🌟 FOMO alert building..."
]

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
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config():
    """Enhanced validation with specific error reporting"""
    if TEST_MODE:
        logging.info("🔧 Running in TEST_MODE - using test bot and test chat ID")

    errors = []
    warnings = []
    ...

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
    
    # Test CoinGecko API with enhanced error handling
    if COINGECKO_API_KEY:
        try:
            test_url = f"{COINGECKO_API}/ping"
            test_params = {'x_cg_pro_api_key': COINGECKO_API_KEY}
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                logging.info("✅ CoinGecko Pro API connection successful")
            elif response.status_code == 401:
                errors.append("COINGECKO_API_KEY is invalid - authentication failed")
            elif response.status_code == 429:
                logging.info("✅ CoinGecko Pro API key works (rate limit hit)")
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
    
    # Log results
    if errors:
        logging.error("❌ CRITICAL CONFIGURATION ERRORS:")
        for error in errors:
            logging.error(f"  - {error}")
    
    if warnings:
        logging.warning("⚠️ Configuration warnings:")
        for warning in warnings:
            logging.warning(f"  - {warning}")
    
    if not errors and not warnings:
        logging.info("✅ Configuration validation passed")
    
    # Stop if critical errors
    if errors:
        raise ValueError(f"Critical configuration errors found: {', '.join(errors)}")
    
    return True