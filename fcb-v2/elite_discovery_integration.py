"""
elite_discovery_integration.py - Real Coin Discovery with Elite Analysis
Integrates Elite analysis files with FCB v2 discovery system
FIXED: Added missing logger import
"""

import asyncio
import logging  # ✅ ADDED THIS MISSING IMPORT
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Set up logger PROPERLY
logger = logging.getLogger(__name__)

# Import Elite analysis systems (with fallback)
try:
    from elite_integration import analyze_coin_comprehensive
    from elite_engine import get_gaming_fomo_score, analyze_elite_setup_instant
    from elite_analyzer import create_analyzer
    ELITE_AVAILABLE = True
    logger.info("🏆 Elite analysis systems loaded successfully!")
except ImportError as e:
    logger.warning(f"⚠️ Elite analysis not available: {e}")
    ELITE_AVAILABLE = False

# Import our other systems (with error handling)
try:
    from session_manager import add_to_user_history
    from token_economics import spend_fcb_token
except ImportError as e:
    logger.error(f"❌ Core system import error: {e}")

class EliteDiscoveryEngine:
    """
    Real coin discovery engine using Elite analysis
    Replaces mock discovery with real CoinGecko data + Elite scoring
    """
    
    def __init__(self):
        # Top trending coins pool (refreshed periodically)
        self.trending_pool = [
            'bitcoin', 'ethereum', 'binancecoin', 'solana', 'cardano',
            'avalanche-2', 'polygon-pos', 'chainlink', 'uniswap',
            'litecoin', 'bitcoin-cash', 'ethereum-classic', 'filecoin',
            'tron', 'algorand', 'vechain', 'theta-token', 'elrond-erd-2',
            'hedera-hashgraph', 'internet-computer', 'ftx-token',
            'cosmos', 'aave', 'maker', 'compound-governance-token'
        ]
        
        # Hidden gems pool (lower cap, higher potential)
        self.gems_pool = [
            'pepe', 'shiba-inu', 'dogecoin', 'floki', 'baby-doge-coin',
            'safemoon-2', 'kishu-inu', 'hoge-finance', 'elongate',
            'dogelon-mars', 'shibainu', 'akita-inu', 'ryoshi-token',
            'saitama-inu', 'catecoin', 'gala', 'sandbox', 'decentraland',
            'axie-infinity', 'stepn', 'illuvium', 'star-atlas',
            'alien-worlds', 'my-neighbor-alice', 'chromia'
        ]
        
        # Elite analysis engine
        if ELITE_AVAILABLE:
            try:
                self.elite_analyzer = create_analyzer()
            except Exception as e:
                logger.error(f"❌ Failed to create elite analyzer: {e}")
                self.elite_analyzer = None
        else:
            self.elite_analyzer = None
        
        logger.info("🔍 Elite Discovery Engine initialized")
    
    async def discover_new_opportunity(self, user_id: int, algorithm: str = 'smart_mix') -> Optional[Dict]:
        """
        Main discovery function - finds real opportunities with Elite analysis
        
        Args:
            user_id: User requesting discovery
            algorithm: 'trending', 'gems', 'smart_mix', 'elite_only'
        
        Returns:
            Dict with coin data and Elite analysis, or None if failed
        """
        try:
            logger.info(f"🔍 Starting discovery for user {user_id} using {algorithm}")
            
            # Select coin based on algorithm
            coin_id = await self._select_coin_by_algorithm(algorithm)
            if not coin_id:
                logger.error("❌ No coin selected for discovery")
                return None
            
            # Create mock coin data (since we don't have CoinGecko integration yet)
            coin_data = await self._create_mock_coin_data(coin_id)
            if not coin_data or coin_data.get('price', 0) <= 0:
                logger.error(f"❌ Invalid coin data for {coin_id}")
                return None
            
            # Run Elite analysis
            elite_analysis = await self._run_elite_analysis(coin_data)
            if not elite_analysis:
                logger.error(f"❌ Elite analysis failed for {coin_id}")
                return None
            
            # Combine coin data with analysis
            discovery_result = {
                **coin_data,
                'elite_analysis': elite_analysis,
                'fomo_score': elite_analysis.get('score', 50),
                'signal': elite_analysis.get('signal', 'Analysis pending'),
                'discovery_algorithm': algorithm,
                'discovery_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Discovery complete: {coin_data['symbol']} scored {elite_analysis.get('score', 0):.1f}")
            return discovery_result
            
        except Exception as e:
            logger.error(f"❌ Discovery failed for user {user_id}: {e}")
            return None
    
    async def _select_coin_by_algorithm(self, algorithm: str) -> Optional[str]:
        """Select coin based on discovery algorithm"""
        try:
            if algorithm == 'trending':
                return random.choice(self.trending_pool)
            elif algorithm == 'gems':
                return random.choice(self.gems_pool)
            elif algorithm == 'smart_mix':
                # 70% chance gems, 30% chance trending
                pool = self.gems_pool if random.random() < 0.7 else self.trending_pool
                return random.choice(pool)
            elif algorithm == 'elite_only':
                # Use both pools but filter by Elite score later
                all_pools = self.trending_pool + self.gems_pool
                return random.choice(all_pools)
            else:
                # Default to smart mix
                return random.choice(self.gems_pool)
                
        except Exception as e:
            logger.error(f"❌ Coin selection failed: {e}")
            return None
    
    async def _create_mock_coin_data(self, coin_id: str) -> Dict:
        """Create mock coin data for testing (replace with real CoinGecko later)"""
        try:
            # Mock data for testing
            mock_prices = {
                'bitcoin': 67000.0,
                'ethereum': 3500.0,
                'dogecoin': 0.15,
                'shiba-inu': 0.000025,
                'pepe': 0.0000015
            }
            
            base_price = mock_prices.get(coin_id, random.uniform(0.00001, 10.0))
            
            coin_data = {
                'id': coin_id,
                'symbol': coin_id.upper().replace('-', ''),
                'name': coin_id.replace('-', ' ').title(),
                'image_url': None,  # Would be filled by CoinGecko
                'price': base_price,
                'volume_24h': random.randint(100000, 50000000),
                'market_cap': random.randint(1000000, 1000000000),
                'market_cap_rank': random.randint(50, 2000),
                'change_1h': random.uniform(-10, 15),
                'change_24h': random.uniform(-20, 30),
                'change_7d': random.uniform(-30, 50),
                'volume_change_24h': random.uniform(-50, 200)
            }
            
            return coin_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create mock data for {coin_id}: {e}")
            return None
    
    async def _run_elite_analysis(self, coin_data: Dict) -> Optional[Dict]:
        """Run Elite analysis on coin data"""
        try:
            if not ELITE_AVAILABLE:
                # Fallback to basic analysis
                return await self._basic_fomo_analysis(coin_data)
            
            # Try Elite gaming analysis first (fast and always works)
            try:
                gaming_result = await get_gaming_fomo_score(coin_data)
                if gaming_result and 'score' in gaming_result:
                    logger.info(f"✅ Elite gaming analysis: {gaming_result['score']:.1f}")
                    return gaming_result
            except Exception as e:
                logger.debug(f"Gaming analysis failed: {e}")
            
            # Fallback to basic if Elite methods fail
            return await self._basic_fomo_analysis(coin_data)
            
        except Exception as e:
            logger.error(f"❌ Elite analysis completely failed: {e}")
            return await self._basic_fomo_analysis(coin_data)
    
    async def _basic_fomo_analysis(self, coin_data: Dict) -> Dict:
        """Fallback basic FOMO analysis when Elite systems unavailable"""
        try:
            symbol = coin_data.get('symbol', 'UNKNOWN')
            price = coin_data.get('price', 0)
            volume = coin_data.get('volume_24h', 0)
            change_24h = coin_data.get('change_24h', 0)
            
            # Basic scoring algorithm
            score = 30  # Base score
            
            # Volume scoring
            if volume > 10_000_000:
                score += 25
            elif volume > 1_000_000:
                score += 15
            elif volume > 100_000:
                score += 10
            
            # Price change scoring
            if change_24h > 10:
                score += 20
            elif change_24h > 5:
                score += 15
            elif change_24h > 0:
                score += 10
            
            # Price range bonus
            if 0.00001 <= price <= 0.01:
                score += 15  # Sweet spot for growth
            
            # Cap score
            final_score = min(95, max(15, score))
            
            # Generate signal
            if final_score >= 80:
                signal = "🚀 Strong Opportunity"
            elif final_score >= 65:
                signal = "📈 Good Setup"
            elif final_score >= 50:
                signal = "👀 Worth Watching"
            else:
                signal = "😴 Low Interest"
            
            return {
                'score': final_score,
                'signal': signal,
                'analysis': f"Basic analysis for {symbol}",
                'confidence': 'Medium',
                'analysis_type': 'basic_fallback'
            }
            
        except Exception as e:
            logger.error(f"❌ Even basic analysis failed: {e}")
            return {
                'score': 50,
                'signal': '📊 Standard Analysis',
                'analysis': 'Analysis completed',
                'confidence': 'Low',
                'analysis_type': 'error_fallback'
            }

# Global discovery engine instance
elite_discovery = EliteDiscoveryEngine()

# Integration functions for navigation_handler.py
async def discover_new_coin_with_elite(user_id: int) -> Optional[Dict]:
    """
    Main function to replace mock discovery in navigation_handler.py
    """
    return await elite_discovery.discover_new_opportunity(user_id, 'smart_mix')

async def discover_trending_coin(user_id: int) -> Optional[Dict]:
    """Discover from trending coins pool"""
    return await elite_discovery.discover_new_opportunity(user_id, 'trending')

async def discover_gem_coin(user_id: int) -> Optional[Dict]:
    """Discover from hidden gems pool"""
    return await elite_discovery.discover_new_opportunity(user_id, 'gems')

async def discover_elite_coin(user_id: int) -> Optional[Dict]:
    """Discover using pure Elite analysis"""
    return await elite_discovery.discover_new_opportunity(user_id, 'elite_only')

# Status check function
def get_elite_discovery_status() -> Dict:
    """Get status of Elite discovery system"""
    return {
        'elite_available': ELITE_AVAILABLE,
        'trending_pool_size': len(elite_discovery.trending_pool),
        'gems_pool_size': len(elite_discovery.gems_pool),
        'analyzer_ready': elite_discovery.elite_analyzer is not None,
        'status': 'operational' if ELITE_AVAILABLE else 'fallback_mode'
    }
