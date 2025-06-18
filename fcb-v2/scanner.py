"""
FCB v2 - Simple Market Scanner
Clean, focused scanner using Elite Analysis
"""

import asyncio
import logging
import aiohttp
from datetime import datetime
from config import COINGECKO_API_KEY, BROADCAST_CHAT_ID
from database import get_subscribed_users
from elite_integration import analyze_coin_comprehensive

logger = logging.getLogger(__name__)

# Scanner settings
SCAN_INTERVAL_HOURS = 4  # Scan every 4 hours
MIN_FOMO_SCORE = 30  # Minimum score to alert (lowered from 80)
MAX_COINS_TO_SCAN = 500  # Scan top 500 coins
EXCLUDED_SYMBOLS = {'usdt', 'usdc', 'busd', 'dai', 'tusd'}  # Skip stablecoins

class SimpleScanner:
    """Simple, clean market scanner"""
    
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        
    async def get_session(self):
        """Get aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_market_data(self, page=1, per_page=250):
        """Fetch market data from CoinGecko Pro API"""
        url = "https://pro-api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc', 
            'per_page': per_page,
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '1h,24h,7d',
            'x_cg_pro_api_key': COINGECKO_API_KEY
        }
        
        session = await self.get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Fetched {len(data)} coins from page {page}")
                    return data
                else:
                    logger.error(f"❌ API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"❌ Market data fetch error: {e}")
            return []
    
    async def scan_for_opportunities(self):
        """Scan market for opportunities using Elite Analysis"""
        logger.info("🔍 Starting market scan...")
        
        opportunities = []
        coins_scanned = 0
        
        try:
            # Scan multiple pages to get good coverage
            for page in range(1, 3):  # Pages 1-2 (top 500 coins)
                coins = await self.fetch_market_data(page=page)
                if not coins:
                    break
                    
                for coin in coins:
                    symbol = coin.get('symbol', '').lower()
                    
                    # Skip stablecoins and invalid coins
                    if symbol in EXCLUDED_SYMBOLS or not coin.get('current_price'):
                        continue
                    
                    try:
                        # Prepare data for Elite Analysis
                        coin_data = {
                            'symbol': coin.get('symbol', '').upper(),
                            'price': coin.get('current_price', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'price_change_percentage_1h': coin.get('price_change_percentage_1h_in_currency', 0),
                            'price_change_percentage_24h': coin.get('price_change_percentage_24h_in_currency', 0),
                            'price_change_percentage_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                            'volume_change_24h': 0  # Default
                        }
                        
                        # Run Elite Analysis
                        result = await analyze_coin_comprehensive(coin_data)
                        score = result.get('fomo_score', 0)
                        
                        coins_scanned += 1
                        logger.info(f"🎯 {symbol.upper()}: {score:.1f}/100")
                        
                        # Check if this is an opportunity
                        if score >= MIN_FOMO_SCORE:
                            opportunity = {
                                'coin_id': coin.get('id'),
                                'symbol': symbol.upper(),
                                'name': coin.get('name'),
                                'price': coin.get('current_price'),
                                'score': score,
                                'signal': result.get('signal', 'Unknown'),
                                'analysis': result.get('analysis', ''),
                                'confidence': result.get('confidence', 'Unknown'),
                                'logo': coin.get('image'),
                                'change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
                                'change_24h': coin.get('price_change_percentage_24h_in_currency', 0),
                                'volume': coin.get('total_volume', 0)
                            }
                            opportunities.append(opportunity)
                            logger.info(f"🔥 OPPORTUNITY: {symbol.upper()} scored {score:.1f}!")
                            
                    except Exception as e:
                        logger.error(f"❌ Error analyzing {symbol.upper()}: {e}")
                        continue
                
                # Add small delay between pages
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Scan error: {e}")
        
        logger.info(f"📊 Scan complete: {coins_scanned} coins analyzed, {len(opportunities)} opportunities found")
        return opportunities
    
    async def format_opportunity_message(self, opp):
        """Format opportunity as Telegram message"""
        symbol = opp['symbol']
        score = opp['score']
        price = opp['price']
        signal = opp['signal']
        change_1h = opp.get('change_1h', 0)
        change_24h = opp.get('change_24h', 0)
        
        # Format price
        if price < 0.01:
            price_str = f"${price:.6f}"
        elif price < 1:
            price_str = f"${price:.4f}"
        else:
            price_str = f"${price:.2f}"
        
        # Create message
        message = f"""🚨 **FOMO ALERT** 🚨

💎 **{symbol}** - {opp.get('name', '')}
📊 **FOMO Score:** {score:.1f}/100
🎯 **Signal:** {signal}
💰 **Price:** {price_str}

📈 **Performance:**
• 1h: {change_1h:+.2f}%
• 24h: {change_24h:+.2f}%

🔍 **Analysis:** {opp.get('analysis', 'Elite analysis detected opportunity')}

⚡ *Powered by Elite Analysis Engine*"""
        
        return message
    
    async def broadcast_opportunities(self, opportunities):
        """Broadcast opportunities to all subscribers"""
        if not opportunities:
            logger.info("📭 No opportunities to broadcast")
            return
        
        # Get subscribers
        subscribers = get_subscribed_users()
        if not subscribers:
            logger.info("👥 No subscribers to notify")
            return
        
        logger.info(f"📢 Broadcasting {len(opportunities)} opportunities to {len(subscribers)} subscribers")
        
        for opp in opportunities:
            message = await self.format_opportunity_message(opp)
            
            # Send to broadcast channel first
            try:
                await self.bot.send_message(BROADCAST_CHAT_ID, message, parse_mode='Markdown')
                logger.info(f"📺 Sent {opp['symbol']} to broadcast channel")
            except Exception as e:
                logger.error(f"❌ Broadcast channel error: {e}")
            
            # Send to individual subscribers
            success_count = 0
            for user_id in subscribers:
                try:
                    await self.bot.send_message(user_id, message, parse_mode='Markdown')
                    success_count += 1
                    await asyncio.sleep(0.05)  # Rate limiting
                except Exception as e:
                    logger.error(f"❌ Failed to send to {user_id}: {e}")
            
            logger.info(f"✅ {opp['symbol']} sent to {success_count}/{len(subscribers)} subscribers")
            await asyncio.sleep(2)  # Delay between different opportunities
    
    async def run_scan_cycle(self):
        """Run one complete scan cycle"""
        start_time = datetime.now()
        logger.info("🚀 Starting scan cycle...")
        
        try:
            # Scan for opportunities
            opportunities = await self.scan_for_opportunities()
            
            # Broadcast opportunities
            if opportunities:
                await self.broadcast_opportunities(opportunities)
            else:
                logger.info("😴 No opportunities found this cycle")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Scan cycle complete in {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Scan cycle error: {e}")
        
        finally:
            # Clean up session if needed
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
    
    async def start_scanning(self):
        """Start continuous scanning loop"""
        logger.info(f"🎯 Starting scanner: scanning every {SCAN_INTERVAL_HOURS} hours")
        
        while True:
            try:
                await self.run_scan_cycle()
                
                # Wait for next cycle
                wait_seconds = SCAN_INTERVAL_HOURS * 3600
                logger.info(f"⏰ Next scan in {SCAN_INTERVAL_HOURS} hours...")
                await asyncio.sleep(wait_seconds)
                
            except Exception as e:
                logger.error(f"❌ Scanner loop error: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)

# Global scanner instance
scanner_instance = None

async def start_scanner(bot):
    """Start the scanner with the bot instance"""
    global scanner_instance
    
    logger.info("🔄 Initializing scanner...")
    scanner_instance = SimpleScanner(bot)
    
    # Start scanning in background
    asyncio.create_task(scanner_instance.start_scanning())
    logger.info("✅ Scanner started successfully!")

async def run_manual_scan(bot):
    """Run a manual scan for testing"""
    logger.info("🧪 Running manual scan...")
    
    scanner = SimpleScanner(bot)
    await scanner.run_scan_cycle()
    
    logger.info("✅ Manual scan complete!")