"""
API Client module for CFB (Crypto FOMO Bot) - PRO API VERSION
Handles all CoinGecko Pro API interactions with optimized session management
Updated with corrected Pro API implementation for real-time data
"""

import aiohttp
import asyncio
import time
import logging
import requests
import difflib
from io import BytesIO

from config import COINGECKO_API, COINGECKO_API_KEY, COIN_SYMBOL_OVERRIDES

# =============================================================================
# PRO API CONFIGURATION
# =============================================================================

# Your validated Pro API key
PRO_API_KEY = "CG-bJP1bqyMemFNQv5dp4nvA9xm"
PRO_API_BASE = "https://pro-api.coingecko.com/api/v3"

# =============================================================================
# ULTRA-FAST SESSION MANAGEMENT
# =============================================================================

session = None

async def get_optimized_session():
    """Ultra-optimized session for maximum speed with Pro API"""
    global session
    if session is None or session.closed:
        # Aggressive timeout settings for speed
        timeout = aiohttp.ClientTimeout(
            total=8,          # Increased slightly for Pro API stability
            connect=2,        # Pro API connection time
            sock_read=6       # Pro API read time
        )
        
        # Aggressive connection pool for maximum throughput
        connector = aiohttp.TCPConnector(
            limit=200,                    
            limit_per_host=100,          
            ttl_dns_cache=300,           
            use_dns_cache=True,
            keepalive_timeout=60,        
            enable_cleanup_closed=True,
            force_close=False,           
        )
        
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'FOMO-Bot-Pro/4.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
    return session

# =============================================================================
# ULTRA-FAST RATE LIMITER (Pro API has higher limits)
# =============================================================================

class OptimizedRateLimiter:
    def __init__(self, calls_per_minute=800):  # Pro API higher limits
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.call_times = []
        self.burst_allowance = 100  # Higher burst for Pro API
        
    async def acquire(self):
        """Ultra-aggressive rate limiter for Pro API"""
        now = time.time()
        
        # Clean old calls (older than 1 minute)
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        # Allow large bursts for ultra-fast initial calls
        if len(self.call_times) < self.burst_allowance:
            self.call_times.append(now)
            return  # No delay for burst calls
        
        # For sustained calls, use minimal delay
        if len(self.call_times) >= self.calls_per_minute:
            sleep_time = 0.075  # Very short sleep for Pro API
            await asyncio.sleep(sleep_time)
        
        self.call_times.append(time.time())

# Global rate limiter instance
rate_limiter = OptimizedRateLimiter(calls_per_minute=800)

# =============================================================================
# ULTRA-FAST BATCH PROCESSING
# =============================================================================

class BatchProcessor:
    def __init__(self, max_concurrent=150, batch_size=75):  # Pro API limits
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, items, process_func):
        """Process items in parallel batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Process batch items concurrently
            batch_tasks = []
            for item in batch:
                task = self._process_with_semaphore(process_func, item)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend([r for r in batch_results if not isinstance(r, Exception)])
            
            # Minimal delay between batches
            await asyncio.sleep(0.05)
        
        return results
    
    async def _process_with_semaphore(self, func, item):
        async with self.semaphore:
            return await func(item)

# Global batch processor
batch_processor = BatchProcessor(max_concurrent=150, batch_size=75)

# =============================================================================
# PRO API FUNCTIONS - CORRECTED IMPLEMENTATIONS
# =============================================================================

async def fetch_coin_data_ultra_fast(coin_id):
    """
    CORRECTED PRO API VERSION: Uses /markets endpoint for real-time data
    This is the proven working implementation from your testing
    """
    try:
        # Correct Pro API endpoint for markets data
        url = f"{PRO_API_BASE}/coins/markets"
        
        # Correct authentication method (URL parameter)
        params = {
            'vs_currency': 'usd',
            'ids': coin_id,
            'order': 'market_cap_desc',
            'per_page': '1',
            'page': '1',
            'sparkline': 'false',
            'price_change_percentage': '1h,24h',
            'x_cg_pro_api_key': PRO_API_KEY  # Proven authentication method
        }
        
        session = await get_optimized_session()
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    coin = data[0]
                    return {
                        'id': coin.get('id'),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name'),
                        'price': coin.get('current_price', 0),
                        'volume': coin.get('total_volume', 0),
                        'market_cap': coin.get('market_cap', 0),
                        'market_cap_rank': coin.get('market_cap_rank', 999),
                        'change_1h': coin.get('price_change_percentage_1h', 0) or 0,
                        'change_24h': coin.get('price_change_percentage_24h', 0) or 0
                    }
            else:
                logging.error(f"Pro API error {response.status} for {coin_id}")
        
        return None
        
    except Exception as e:
        logging.error(f"Pro API fetch error for {coin_id}: {e}")
        return None

async def fetch_market_data_ultra_fast(page=1, per_page=250):
    """Blazing fast market data with Pro API"""
    url = f"{PRO_API_BASE}/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': per_page,
        'page': page,
        'sparkline': 'false',
        'price_change_percentage': '1h,24h',
        'x_cg_pro_api_key': PRO_API_KEY
    }
    
    session = await get_optimized_session()
    try:
        async with session.get(url, params=params) as response:
            if response.status == 429:
                await asyncio.sleep(0.1)
                return []
            if response.status == 200:
                return await response.json()
            return []
    except asyncio.TimeoutError:
        logging.warning(f"Timeout on market data page {page}")
        return []
    except Exception as e:
        logging.debug(f"Market data error: {e}")
        return []

async def fetch_ohlcv_data_ultra_fast(coin_id, days=7):
    """Ultra-fast OHLCV with Pro API"""
    url = f"{PRO_API_BASE}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd", 
        "days": days, 
        "interval": "daily",
        "x_cg_pro_api_key": PRO_API_KEY
    }
    
    session = await get_optimized_session()
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return None
    except:
        return None

async def fetch_ticker_data_ultra_fast(coin_id):
    """Ultra-fast ticker data with Pro API"""
    url = f"{PRO_API_BASE}/coins/{coin_id}/tickers"
    params = {"x_cg_pro_api_key": PRO_API_KEY}
    
    session = await get_optimized_session()
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return None
    except:
        return None

async def get_coin_info_ultra_fast(query):
    """Ultra-fast coin lookup with Pro API search and data fetch"""
    try:
        query_lower = query.lower()
        
        # Check symbol overrides first (instant)
        if query_lower in COIN_SYMBOL_OVERRIDES:
            coin_id = COIN_SYMBOL_OVERRIDES[query_lower]
        else:
            # Fast search lookup with Pro API
            search_url = f"{PRO_API_BASE}/search"
            params = {"query": query, "x_cg_pro_api_key": PRO_API_KEY}
            
            session = await get_optimized_session()
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    search_data = await response.json()
                    coins = search_data.get('coins', [])
                    if coins:
                        coin_id = coins[0]['id']
                    else:
                        return None, None
                else:
                    return None, None
        
        # Fetch coin data using the corrected function
        coin_data_markets = await fetch_coin_data_ultra_fast(coin_id)
        if coin_data_markets:
            # Convert markets data to standard format
            coin_info = {
                'id': coin_data_markets['id'],
                'name': coin_data_markets['name'],
                'symbol': coin_data_markets['symbol'],
                'logo': None,  # Markets endpoint doesn't include logo
                'price': coin_data_markets['price'],
                'change_1h': coin_data_markets['change_1h'],
                'change_24h': coin_data_markets['change_24h'],
                'market_cap': coin_data_markets['market_cap'],
                'volume': coin_data_markets['volume'],
                'cmc_rank': coin_data_markets['market_cap_rank'],
                'source_url': f'https://www.coingecko.com/en/coins/{coin_id}',
            }
            return coin_id, coin_info
        
        # Fallback to detailed endpoint for logo if needed
        detail_url = f"{PRO_API_BASE}/coins/{coin_id}"
        params = {"x_cg_pro_api_key": PRO_API_KEY}
        
        session = await get_optimized_session()
        async with session.get(detail_url, params=params) as response:
            if response.status == 200:
                detail_data = await response.json()
                market_data = detail_data.get('market_data', {})
                coin_info = {
                    'id': coin_id,
                    'name': detail_data.get('name', 'Unknown'),
                    'symbol': detail_data.get('symbol', '').upper(),
                    'logo': detail_data.get('image', {}).get('large'),
                    'price': market_data.get('current_price', {}).get('usd', 0),
                    'change_1h': market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 0),
                    'change_24h': market_data.get('price_change_percentage_24h_in_currency', {}).get('usd', 0),
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                    'volume': market_data.get('total_volume', {}).get('usd', 0),
                    'cmc_rank': detail_data.get('market_cap_rank'),
                    'source_url': f'https://www.coingecko.com/en/coins/{coin_id}',
                }
                return coin_id, coin_info
        
        return None, None
        
    except Exception as e:
        logging.error(f'Ultra-fast Pro API lookup failed for {query}: {e}')
        return None, None

# =============================================================================
# FALLBACK SYNC FUNCTIONS (FOR COMPATIBILITY) - Updated with Pro API
# =============================================================================

def fuzzy_find_coin(query, all_coins):
    """Find coin using fuzzy matching"""
    choices, id_map = [], {}
    for c in all_coins:
        for field in [c['id'], c['symbol'], c['name'].lower()]:
            choices.append(field)
            id_map[field] = c
    best_matches = difflib.get_close_matches(query, choices, n=1, cutoff=0.7)
    return id_map[best_matches[0]] if best_matches else None

def fetch_ohlcv_data(coin_id, days=7):
    """Sync fallback OHLCV fetching with Pro API"""
    url = f"{PRO_API_BASE}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd", 
        "days": days, 
        "interval": "daily",
        "x_cg_pro_api_key": PRO_API_KEY
    }
    
    try:
        logging.info(f"Fetching OHLCV for {coin_id}")
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 429:
            logging.warning(f"Rate limit for OHLCV: {coin_id}")
            time.sleep(2)
            return None
        response.raise_for_status()
        data = response.json()
        logging.info(f"OHLCV data retrieved for {coin_id}")
        return data
    except requests.exceptions.Timeout:
        logging.error(f"OHLCV timeout for {coin_id}")
        return None
    except Exception as e:
        logging.warning(f"Error fetching OHLCV for {coin_id}: {e}")
        return None

def fetch_from_coingecko(query):
    """Enhanced coin lookup with Pro API and better error handling"""
    url_list = f'{PRO_API_BASE}/coins/list'
    url_data = f"{PRO_API_BASE}/coins/{{}}"
    
    try:
        # Get coins list with Pro API
        for attempt in range(3):
            try:
                params = {'x_cg_pro_api_key': PRO_API_KEY}
                all_coins_response = requests.get(url_list, params=params, timeout=15)
                all_coins_response.raise_for_status()
                all_coins = all_coins_response.json()
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    logging.error("Timeout fetching coins list after 3 attempts")
                    return None, None
                time.sleep(2)
            except Exception as e:
                logging.error(f"Error fetching coins list (attempt {attempt + 1}): {e}")
                if attempt == 2:
                    return None, None
                time.sleep(2)
        
        query_lower = query.lower()
        
        # Find coin ID
        if query_lower in COIN_SYMBOL_OVERRIDES:
            cg_id = COIN_SYMBOL_OVERRIDES[query_lower]
        else:
            match = next((c for c in all_coins if c['id'] == query_lower or c['symbol'] == query_lower or c['name'].lower() == query_lower), None)
            if not match:
                match = next((c for c in all_coins if query_lower in c['name'].lower()), None)
            if not match:
                match = fuzzy_find_coin(query_lower, all_coins)
            if not match:
                logging.warning(f"No match found for query: {query}")
                return None, None
            cg_id = match['id']
        
        # Fetch coin data with Pro API
        params = {'x_cg_pro_api_key': PRO_API_KEY}
            
        for attempt in range(3):
            try:
                data_response = requests.get(url_data.format(cg_id), params=params, timeout=15)
                
                if data_response.status_code == 429:
                    logging.warning(f"Rate limit hit for {cg_id}, attempt {attempt + 1}")
                    time.sleep(3 * (attempt + 1))  # Shorter backoff for Pro API
                    continue
                    
                data_response.raise_for_status()
                data = data_response.json()
                
                if 'error' in data:
                    logging.error(f"CoinGecko Pro API error for {cg_id}: {data['error']}")
                    return None, None
                
                break
                
            except requests.exceptions.Timeout:
                if attempt == 2:
                    logging.error(f"Timeout fetching data for {cg_id} after 3 attempts")
                    return None, None
                time.sleep(2)
            except Exception as e:
                logging.error(f"Error fetching data for {cg_id} (attempt {attempt + 1}): {e}")
                if attempt == 2:
                    return None, None
                time.sleep(2)
        
        # Parse coin data safely
        market_data = data.get('market_data', {})
        coin_info = {
            'id': cg_id,
            'name': data.get('name', 'Unknown'),
            'symbol': data.get('symbol', '').upper(),
            'logo': data.get('image', {}).get('large'),
            'price': market_data.get('current_price', {}).get('usd', 0),
            'change_1h': market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 0),
            'change_24h': market_data.get('price_change_percentage_24h_in_currency', {}).get('usd', 0),
            'market_cap': market_data.get('market_cap', {}).get('usd', 0),
            'volume': market_data.get('total_volume', {}).get('usd', 0),
            'cmc_rank': data.get('market_cap_rank'),
            'source_url': f'https://www.coingecko.com/en/coins/{cg_id}',
        }
        
        return cg_id, coin_info
        
    except Exception as e:
        logging.error(f'CoinGecko Pro API fetch failed for {query}: {e}')
        return None, None

def get_coin_info(query):
    """Standard coin info lookup with Pro API"""
    cg_id, cg_data = fetch_from_coingecko(query)
    if cg_data:
        cg_data['source'] = 'coingecko'
        return cg_id, cg_data
    return None, None

# =============================================================================
# SESSION CLEANUP
# =============================================================================

async def cleanup_session():
    """Clean up the global session"""
    global session
    if session and not session.closed:
        await session.close()

# =============================================================================
# AUTOMATIC CLEANUP ON EXIT
# =============================================================================

import atexit

def sync_cleanup():
    """Synchronous cleanup for atexit"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.run_until_complete(cleanup_session())
    except:
        pass

# Register cleanup on exit
atexit.register(sync_cleanup)