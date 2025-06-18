"""
coin_image_handler.py - CoinGecko Image Integration
Fetches and displays professional coin logos like FCB v1
"""

import aiohttp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CoinImageHandler:
    """Handle CoinGecko coin image fetching and caching"""
    
    def __init__(self):
        self.image_cache = {}  # Cache images to avoid repeated API calls
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
    
    async def get_coin_image_url(self, coin_id: str, symbol: str = None) -> Optional[str]:
        """
        Get CoinGecko image URL for a coin
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            symbol: Coin symbol as fallback (e.g., 'BTC', 'ETH')
        
        Returns:
            Image URL or None if not found
        """
        try:
            # Check cache first
            cache_key = coin_id.lower()
            if cache_key in self.image_cache:
                return self.image_cache[cache_key]
            
            # Try to get coin data from CoinGecko
            async with aiohttp.ClientSession() as session:
                url = f"{self.coingecko_base_url}/coins/{coin_id}"
                
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract image URL
                        image_url = None
                        if 'image' in data:
                            # Prefer large image, fallback to smaller
                            image_url = (data['image'].get('large') or 
                                       data['image'].get('small') or 
                                       data['image'].get('thumb'))
                        
                        if image_url:
                            # Cache the result
                            self.image_cache[cache_key] = image_url
                            logger.info(f"✅ Got image for {coin_id}: {image_url}")
                            return image_url
                        else:
                            logger.warning(f"⚠️ No image found for {coin_id}")
                            return None
                    else:
                        logger.warning(f"⚠️ CoinGecko API error for {coin_id}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error fetching image for {coin_id}: {e}")
            return None
    
    async def get_coin_data_with_image(self, coin_id: str) -> Dict:
        """
        Get comprehensive coin data including image from CoinGecko
        
        Returns:
            Dictionary with coin data including image_url
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.coingecko_base_url}/coins/{coin_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract key data for FCB analysis
                        coin_data = {
                            'id': data.get('id'),
                            'symbol': data.get('symbol', '').upper(),
                            'name': data.get('name'),
                            'image_url': None,
                            'price': 0,
                            'volume_24h': 0,
                            'market_cap': 0,
                            'market_cap_rank': data.get('market_cap_rank'),
                            'change_1h': 0,
                            'change_24h': 0,
                            'change_7d': 0,
                            'volume_change_24h': 0
                        }
                        
                        # Extract image
                        if 'image' in data:
                            coin_data['image_url'] = (data['image'].get('large') or 
                                                    data['image'].get('small') or 
                                                    data['image'].get('thumb'))
                        
                        # Extract market data
                        if 'market_data' in data:
                            market_data = data['market_data']
                            
                            # Price in USD
                            if 'current_price' in market_data and 'usd' in market_data['current_price']:
                                coin_data['price'] = float(market_data['current_price']['usd'])
                            
                            # Volume 24h in USD
                            if 'total_volume' in market_data and 'usd' in market_data['total_volume']:
                                coin_data['volume_24h'] = float(market_data['total_volume']['usd'])
                            
                            # Market cap in USD
                            if 'market_cap' in market_data and 'usd' in market_data['market_cap']:
                                coin_data['market_cap'] = float(market_data['market_cap']['usd'])
                            
                            # Price changes
                            coin_data['change_1h'] = market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 0) or 0
                            coin_data['change_24h'] = market_data.get('price_change_percentage_24h', 0) or 0
                            coin_data['change_7d'] = market_data.get('price_change_percentage_7d', 0) or 0
                            
                            # Volume change
                            coin_data['volume_change_24h'] = market_data.get('volume_change_24h', 0) or 0
                        
                        logger.info(f"✅ Got complete data for {coin_id}: {coin_data['name']} (${coin_data['price']})")
                        return coin_data
                        
                    else:
                        logger.error(f"❌ CoinGecko API error for {coin_id}: {response.status}")
                        return self._create_fallback_coin_data(coin_id)
                        
        except Exception as e:
            logger.error(f"❌ Error fetching coin data for {coin_id}: {e}")
            return self._create_fallback_coin_data(coin_id)
    
    def _create_fallback_coin_data(self, coin_id: str) -> Dict:
        """Create fallback coin data when API fails"""
        return {
            'id': coin_id,
            'symbol': coin_id.upper(),
            'name': f"{coin_id.title()} Token",
            'image_url': None,
            'price': 0.001,
            'volume_24h': 1_000_000,
            'market_cap': 10_000_000,
            'market_cap_rank': 999,
            'change_1h': 0,
            'change_24h': 0,
            'change_7d': 0,
            'volume_change_24h': 0,
            'fallback': True
        }

# Global image handler instance
coin_image_handler = CoinImageHandler()

# Convenience functions
async def get_coin_image_url(coin_id: str, symbol: str = None) -> Optional[str]:
    """Get coin image URL from CoinGecko"""
    return await coin_image_handler.get_coin_image_url(coin_id, symbol)

async def get_coin_data_with_image(coin_id: str) -> Dict:
    """Get complete coin data including image"""
    return await coin_image_handler.get_coin_data_with_image(coin_id)

# Integration with existing UI formatters
def format_coin_card_with_image(coin_data: Dict, fomo_analysis: Dict) -> str:
    """
    Format coin card with image like FCB v1 screenshot
    """
    try:
        # Get coin details
        symbol = coin_data.get('symbol', 'UNKNOWN').upper()
        name = coin_data.get('name', 'Unknown Token')
        price = coin_data.get('price', 0)
        fomo_score = fomo_analysis.get('score', 0)
        signal = fomo_analysis.get('signal', 'Analysis pending')
        
        # Build card message
        card_message = ""
        
        # Add image if available (Telegram will display it)
        image_url = coin_data.get('image_url')
        if image_url:
            card_message += f"🖼️ [Coin Image]({image_url})\n\n"
        
        # Coin header (matching FCB v1 style)
        card_message += f"🚀 **{name} ({symbol})**\n\n"
        
        # FOMO score (EXACT FCB v1 style)
        card_message += f"**FOMO: {fomo_score:.2f}%**\n"
        
        # Analysis result (EXACT FCB v1 style)
        card_message += f"⚡ {signal}\n\n"
        
        # Price and details
        card_message += f"💰 **Price:** ${price:.8f}\n"
        card_message += f"📊 **Volume:** ${coin_data.get('volume_24h', 0):,.0f}\n"
        card_message += f"🏆 **Market Cap:** ${coin_data.get('market_cap', 0):,.0f}\n\n"
        
        return card_message
        
    except Exception as e:
        logger.error(f"Error formatting coin card: {e}")
        return f"🪙 **{coin_data.get('symbol', 'ERROR')}**\n❌ Display error"