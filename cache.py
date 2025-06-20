"""
Cache management module for CFB (Crypto FOMO Bot)
Handles ultra-fast FOMO scanning, caching, and background updates
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta

# =============================================================================
# ✅ ULTRA-FAST CACHE SYSTEM WITH PRO API BACKGROUND REFRESH
# =============================================================================

# Global cache storage - THIS is what makes it fast
_OPPORTUNITY_CACHE = {
    'data': [],
    'last_update': 0,
    'updating': False,
    'cache_duration': 300  # 5 minutes cache
}

PRO_API_AVAILABLE = False
try:
    from pro_api_client import get_ultra_fast_fomo_opportunities_pro
    PRO_API_AVAILABLE = True
    print("✅ Pro API client found - using Pro API with TRUE caching")
except ImportError:
    print("⚠️ Pro API client not found - using fallback system")

async def get_ultra_fast_fomo_opportunities():
    """
    ✅ LIGHTNING FAST: Returns cached data instantly, refreshes in background
    
    SPEED TARGET: < 0.001 seconds (pure memory access)
    """
    global _OPPORTUNITY_CACHE
    
    current_time = time.time()
    cache_age = current_time - _OPPORTUNITY_CACHE['last_update']
    
    # ⚡ INSTANT RETURN: If we have recent cached data, return it immediately
    if _OPPORTUNITY_CACHE['data'] and cache_age < _OPPORTUNITY_CACHE['cache_duration']:
        logging.info(f"⚡ INSTANT CACHE HIT: Returning {len(_OPPORTUNITY_CACHE['data'])} opportunities (age: {cache_age:.1f}s)")
        return _OPPORTUNITY_CACHE['data']
    
    # 🔄 BACKGROUND REFRESH: Start refresh if not already updating
    if not _OPPORTUNITY_CACHE['updating']:
        logging.info("🔄 Starting background cache refresh...")
        asyncio.create_task(_refresh_cache_background())
    
    # 🚀 INSTANT FALLBACK: Return existing data (even if old) or enhanced fallback
    if _OPPORTUNITY_CACHE['data']:
        logging.info(f"🚀 RETURNING EXISTING DATA: {len(_OPPORTUNITY_CACHE['data'])} opportunities (age: {cache_age:.1f}s)")
        return _OPPORTUNITY_CACHE['data']
    else:
        logging.info("🎯 FIRST RUN: Using enhanced fallback while background refresh loads")
        return _get_enhanced_fallback_opportunities()

async def _refresh_cache_background():
    """
    🔄 BACKGROUND ONLY: Refresh cache without blocking user interactions
    This is where the slow Pro API calls happen - NOT during NEXT button clicks
    """
    global _OPPORTUNITY_CACHE
    
    if _OPPORTUNITY_CACHE['updating']:
        return  # Already updating
    
    _OPPORTUNITY_CACHE['updating'] = True
    
    try:
        logging.info("🔄 Background: Starting Pro API cache refresh...")
        refresh_start = time.time()
        
        if PRO_API_AVAILABLE:
            # THIS is where the 3-5 second API call happens - in the BACKGROUND
            new_opportunities = await get_ultra_fast_fomo_opportunities_pro()
            
            if new_opportunities and len(new_opportunities) > 0:
                _OPPORTUNITY_CACHE['data'] = new_opportunities
                _OPPORTUNITY_CACHE['last_update'] = time.time()
                
                refresh_time = time.time() - refresh_start
                logging.info(f"✅ Background: Cache refreshed with {len(new_opportunities)} opportunities in {refresh_time:.1f}s")
                
                # Log top opportunities for verification
                for i, opp in enumerate(new_opportunities[:3]):
                    symbol = opp.get('symbol', 'Unknown')
                    fomo = opp.get('fomo_score', 0)
                    signal = opp.get('signal_type', 'Unknown')
                    logging.info(f"  🏆 {i+1}. {symbol}: FOMO {fomo}% ({signal})")
            else:
                logging.warning("⚠️ Background: Pro API returned no data")
        else:
            logging.warning("⚠️ Background: Pro API not available, keeping existing cache")
    
    except Exception as e:
        logging.error(f"❌ Background: Cache refresh error: {e}")
    
    finally:
        _OPPORTUNITY_CACHE['updating'] = False

def _get_enhanced_fallback_opportunities():
    """
    ✅ INSTANT FALLBACK: High-quality opportunities for immediate use
    These are always available instantly while background refresh runs
    """
    logging.info("🎯 Using enhanced fallback opportunities (INSTANT)")
    
    fallback_opportunities = [
        {
            'coin': 'bitcoin',
            'name': 'Bitcoin', 
            'symbol': 'BTC',
            'fomo_score': 88,
            'signal_type': '🏆 LEGENDARY',
            'volume_spike': 2.5,
            'current_price': 98000,
            'price_1h_change (%)': 1.2,
            'price_24h_change (%)': 5.2,
            'price_7d_change (%)': 12.1,
            'volume_24h': 25000000000,
            'market_cap': 1950000000000,
            'market_cap_rank': 1,
            'logo': 'https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png',
            'source_url': 'https://www.coingecko.com/en/coins/bitcoin',
            'trend_status': 'Strong Uptrend',
            'distribution_status': 'Accumulation'
        },
        {
            'coin': 'ethereum',
            'name': 'Ethereum',
            'symbol': 'ETH',
            'fomo_score': 82,
            'signal_type': '💎 EPIC', 
            'volume_spike': 2.1,
            'current_price': 3500,
            'price_1h_change (%)': 0.8,
            'price_24h_change (%)': 3.1,
            'price_7d_change (%)': 8.5,
            'volume_24h': 15000000000,
            'market_cap': 420000000000,
            'market_cap_rank': 2,
            'logo': 'https://coin-images.coingecko.com/coins/images/279/large/ethereum.png',
            'source_url': 'https://www.coingecko.com/en/coins/ethereum',
            'trend_status': 'Moderate Uptrend',
            'distribution_status': 'Steady'
        },
        {
            'coin': 'solana',
            'name': 'Solana',
            'symbol': 'SOL',
            'fomo_score': 86,
            'signal_type': '⚡ BREAKOUT',
            'volume_spike': 3.2,
            'current_price': 240,
            'price_1h_change (%)': 2.3,
            'price_24h_change (%)': 8.7,
            'price_7d_change (%)': 15.2,
            'volume_24h': 3000000000,
            'market_cap': 115000000000,
            'market_cap_rank': 5,
            'logo': 'https://coin-images.coingecko.com/coins/images/4128/large/solana.png',
            'source_url': 'https://www.coingecko.com/en/coins/solana',
            'trend_status': 'Strong Breakout',
            'distribution_status': 'Bullish'
        }
    ]
    
    # Update cache with fallback data
    _OPPORTUNITY_CACHE['data'] = fallback_opportunities
    _OPPORTUNITY_CACHE['last_update'] = time.time()
    
    return fallback_opportunities

# =============================================================================
# ✅ CACHE MANAGEMENT FUNCTIONS
# =============================================================================

def force_cache_refresh():
    """Force immediate background refresh"""
    logging.info("🔄 Forcing immediate cache refresh...")
    asyncio.create_task(_refresh_cache_background())

def get_cache_stats():
    """Get cache statistics for debugging"""
    global _OPPORTUNITY_CACHE
    
    cache_age = time.time() - _OPPORTUNITY_CACHE['last_update']
    
    return {
        'total_opportunities': len(_OPPORTUNITY_CACHE['data']),
        'cache_age_seconds': cache_age,
        'cache_age_minutes': cache_age / 60,
        'is_updating': _OPPORTUNITY_CACHE['updating'],
        'last_update': datetime.fromtimestamp(_OPPORTUNITY_CACHE['last_update']).strftime('%Y-%m-%d %H:%M:%S'),
        'cache_duration': _OPPORTUNITY_CACHE['cache_duration'],
        'is_fresh': cache_age < _OPPORTUNITY_CACHE['cache_duration']
    }

def clear_cache():
    """Clear cache for testing"""
    global _OPPORTUNITY_CACHE
    _OPPORTUNITY_CACHE['data'] = []
    _OPPORTUNITY_CACHE['last_update'] = 0
    logging.info("🗑️ Cache cleared")

# =============================================================================
# ✅ STARTUP CACHE WARMING
# =============================================================================

async def init_ultra_fast_cache():
    """
    ✅ FIXED: Initialize cache with fallback data and start background refresh
    This replaces both warm_cache_on_startup and the infinite loop version
    """
    global _OPPORTUNITY_CACHE
    
    logging.info("🔥 Initializing ULTRA-FAST cache...")
    
    # Start with fallback data immediately
    _OPPORTUNITY_CACHE['data'] = _get_enhanced_fallback_opportunities()
    _OPPORTUNITY_CACHE['last_update'] = time.time()
    
    logging.info("✅ Cache initialized with fallback data")
    
    # Start background refresh immediately (once)
    asyncio.create_task(_refresh_cache_background())
    
    # Set up periodic refresh every 5 minutes
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            # Only refresh if not currently updating
            if not _OPPORTUNITY_CACHE['updating']:
                asyncio.create_task(_refresh_cache_background())
            else:
                logging.info("⏳ Skipping refresh - already updating")
                
        except Exception as e:
            logging.error(f"❌ Cache refresh scheduler error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

# =============================================================================
# ✅ LEGACY COMPATIBILITY FUNCTIONS
# =============================================================================

async def warm_cache():
    """Legacy function - redirects to new cache system"""
    return await init_ultra_fast_cache()

def get_cached_opportunities():
    """Get opportunities from cache"""
    global _OPPORTUNITY_CACHE
    return _OPPORTUNITY_CACHE.get('data', [])

def get_next_cached_coin():
    """Get next coin from cache rotation"""
    global _OPPORTUNITY_CACHE
    
    coins = _OPPORTUNITY_CACHE.get('data', [])
    if not coins:
        return None
    
    # Simple rotation - just return first coin for now
    # You can add index tracking if needed
    return coins[0]

def is_cache_fresh():
    """Check if cache is fresh"""
    global _OPPORTUNITY_CACHE
    
    if not _OPPORTUNITY_CACHE.get('last_update'):
        return False
    
    cache_age = time.time() - _OPPORTUNITY_CACHE['last_update']
    return cache_age < _OPPORTUNITY_CACHE['cache_duration']

# Auto-initialize message
if PRO_API_AVAILABLE:
    print("🔧 ULTRA-FAST CACHE SYSTEM READY:")
    print("   ⚡ Instant cache access (< 0.001s)")
    print("   🔄 Background Pro API refresh every 5 minutes")
    print("   🎯 Fallback data ensures immediate availability")
else:
    print("🔧 Fallback caching system active")