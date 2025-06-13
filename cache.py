"""
Cache management module for CFB (Crypto FOMO Bot)
Handles ultra-fast FOMO scanning, caching, and background updates
"""

import asyncio
import logging
import time
from datetime import datetime

from config import (
    STABLECOIN_SYMBOLS, TOP_N_TO_EXCLUDE, MAX_COINS_PER_PAGE,
    CACHE_REFRESH_INTERVAL, FOMO_CACHE
)
from api_client import fetch_market_data_ultra_fast, batch_processor
from analysis import calculate_fomo_status_ultra_fast

# =============================================================================
# ULTRA-FAST MARKET SCANNING FOR CACHE
# =============================================================================

async def get_ultra_fast_fomo_opportunities():
    """Ultra-fast FOMO scanning using maximum parallel processing"""
    start_time = time.time()
    logging.info("Starting ULTRA-FAST FOMO scan with maximum parallelization...")
    
    # Get exclusion list quickly
    top_symbols_data = await fetch_market_data_ultra_fast(page=1, per_page=TOP_N_TO_EXCLUDE)
    top_symbols = set(t['symbol'].lower() for t in top_symbols_data)
    excluded_symbols = STABLECOIN_SYMBOLS | top_symbols
    
    opportunities = []
    candidate_coins = []
    
    # PHASE 1: Rapid parallel page fetching
    page_tasks = []
    for page in range(1, 15):  # Increased coverage
        task = fetch_market_data_ultra_fast(page=page, per_page=MAX_COINS_PER_PAGE)
        page_tasks.append(task)
    
    # Fetch all pages in parallel
    logging.info("Fetching market data in parallel...")
    page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
    
    # Process results and filter candidates
    for page_data in page_results:
        if isinstance(page_data, Exception) or not page_data:
            continue
            
        for coin in page_data:
            symbol = coin.get('symbol', '').lower()
            if symbol in excluded_symbols:
                continue
            
            market_cap = coin.get('market_cap', 0)
            if market_cap is None or market_cap > 50_000_000:
                continue
            
            volume = coin.get('total_volume', 0) or 0
            if volume < 50_000:
                continue
            
            # Quick pre-screening
            price_24h_change = abs(coin.get('price_change_percentage_24h_in_currency', 0) or 0)
            if price_24h_change > 100:  # Skip extreme pumps
                continue
            
            candidate_coins.append(coin)
    
    logging.info(f"Found {len(candidate_coins)} candidates from parallel page fetching")
    
    # PHASE 2: Parallel FOMO analysis on candidates
    if candidate_coins:
        # Sort by volume and take top candidates
        candidate_coins.sort(key=lambda x: x.get('total_volume', 0), reverse=True)
        top_candidates = candidate_coins[:300]  # Increased capacity
        
        # Process in parallel using batch processor
        async def analyze_candidate(coin):
            try:
                # Convert coin format
                coin_data = {
                    'id': coin.get('id', ''),
                    'name': coin.get('name', ''),
                    'symbol': coin.get('symbol', ''),
                    'price': coin.get('current_price', 0),
                    'change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
                    'change_24h': coin.get('price_change_percentage_24h_in_currency', 0),
                    'volume': coin.get('total_volume', 0)
                }
                
                fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast(coin_data)
                
                if fomo_score >= 30:  # Lower threshold for more variety
                    return {
                        'coin': coin.get('id', ''),
                        'symbol': coin.get('symbol', ''),
                        'name': coin.get('name', ''),
                        'current_price': coin.get('current_price', 0),
                        'price_1h_change (%)': coin_data['change_1h'],
                        'price_24h_change (%)': coin_data['change_24h'],
                        'volume_24h': coin_data['volume'],
                        'volume_spike': volume_spike,
                        'fomo_score': fomo_score,
                        'signal_type': signal_type,
                        'trend_status': trend_status,
                        'distribution_status': distribution_status,
                        'logo': coin.get('image'),
                        'source_url': f'https://www.coingecko.com/en/coins/{coin.get("id", "")}'
                    }
                return None
            except Exception as e:
                logging.debug(f"Error analyzing {coin.get('symbol', 'unknown')}: {e}")
                return None
        
        logging.info("Running parallel FOMO analysis...")
        opportunities = await batch_processor.process_batch(top_candidates, analyze_candidate)
        opportunities = [opp for opp in opportunities if opp is not None]
    
    # Sort and return top opportunities
    opportunities.sort(key=lambda x: x['fomo_score'], reverse=True)
    
    elapsed = time.time() - start_time
    logging.info(f"✅ ULTRA-FAST scan complete! Found {len(opportunities)} opportunities in {elapsed:.1f}s (was ~60s before)")
    
    return opportunities[:100]  # Return more opportunities

# =============================================================================
# ULTRA-FAST CACHE MANAGEMENT
# =============================================================================

async def init_ultra_fast_cache():
    """Initialize and maintain ultra-fast FOMO cache"""
    global FOMO_CACHE
    
    while True:
        try:
            logging.info("Refreshing ULTRA-FAST cache...")
            
            opportunities = await get_ultra_fast_fomo_opportunities()
            
            if opportunities:
                FOMO_CACHE['coins'] = opportunities
                FOMO_CACHE['last_update'] = datetime.now()
                FOMO_CACHE['current_index'] = 0
                
                logging.info(f"✅ Cache updated with {len(opportunities)} opportunities")
            
            await asyncio.sleep(CACHE_REFRESH_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error updating cache: {e}")
            await asyncio.sleep(60)

# =============================================================================
# CACHE UTILITY FUNCTIONS
# =============================================================================

def get_cached_opportunities():
    """Get opportunities from cache"""
    global FOMO_CACHE
    return FOMO_CACHE.get('coins', [])

def get_next_cached_coin():
    """Get next coin from cache rotation"""
    global FOMO_CACHE
    
    if not FOMO_CACHE.get('coins'):
        return None
    
    current_index = FOMO_CACHE.get('current_index', 0)
    if current_index >= len(FOMO_CACHE['coins']):
        FOMO_CACHE['current_index'] = 0
        current_index = 0
    
    coin_data = FOMO_CACHE['coins'][current_index]
    FOMO_CACHE['current_index'] = current_index + 1
    
    return coin_data

def is_cache_fresh():
    """Check if cache is fresh (updated recently)"""
    global FOMO_CACHE
    
    if not FOMO_CACHE.get('last_update'):
        return False
    
    time_since_update = (datetime.now() - FOMO_CACHE['last_update']).total_seconds()
    return time_since_update < CACHE_REFRESH_INTERVAL * 2  # Allow 2x the refresh interval

def get_cache_stats():
    """Get cache statistics for debugging"""
    global FOMO_CACHE
    
    return {
        'total_coins': len(FOMO_CACHE.get('coins', [])),
        'current_index': FOMO_CACHE.get('current_index', 0),
        'last_update': FOMO_CACHE.get('last_update'),
        'is_fresh': is_cache_fresh()
    }

# =============================================================================
# CACHE WARMING FUNCTIONS
# =============================================================================

async def warm_cache():
    """Warm the cache on startup"""
    logging.info("Warming cache on startup...")
    
    try:
        opportunities = await get_ultra_fast_fomo_opportunities()
        
        if opportunities:
            global FOMO_CACHE
            FOMO_CACHE['coins'] = opportunities
            FOMO_CACHE['last_update'] = datetime.now()
            FOMO_CACHE['current_index'] = 0
            
            logging.info(f"✅ Cache warmed with {len(opportunities)} opportunities")
        else:
            logging.warning("⚠️ Cache warming found no opportunities")
            
    except Exception as e:
        logging.error(f"❌ Error warming cache: {e}")

async def force_cache_refresh():
    """Force an immediate cache refresh"""
    logging.info("🔄 Forcing cache refresh...")
    
    try:
        opportunities = await get_ultra_fast_fomo_opportunities()
        
        if opportunities:
            global FOMO_CACHE
            FOMO_CACHE['coins'] = opportunities
            FOMO_CACHE['last_update'] = datetime.now()
            FOMO_CACHE['current_index'] = 0
            
            logging.info(f"✅ Cache force-refreshed with {len(opportunities)} opportunities")
            return True
        else:
            logging.warning("⚠️ Force refresh found no opportunities")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error force-refreshing cache: {e}")
        return False