"""
analysis/patterns.py - Advanced Pattern Detection & New Token Analysis
Part 2 of 4: Enhanced pattern recognition and new token detection systems

FEATURES:
- New token detection (ranking-based bonuses)
- Dynamic volume thresholds by market cap  
- DEX trading detection
- Predictive analysis patterns
- Enhanced signal types for new tokens
"""

import statistics
import asyncio
import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from api_client import (
    fetch_ohlcv_data_ultra_fast, fetch_ticker_data_ultra_fast
)

# =============================================================================
# NEW TOKEN DETECTION SYSTEM
# =============================================================================

class NewTokenDetector:
    """Detect recently launched tokens - SAFE ADDITION"""
    
    def __init__(self):
        self.new_token_cache = {}
        self.last_update = datetime.now() - timedelta(hours=1)
        self.min_ranking_threshold = 1500  # Catch tokens like Derive (#800)
        self.new_token_days = 60
        
    async def check_if_new_token(self, coin_id: str, coin_symbol: str, market_cap_rank: int = None) -> Tuple[int, str]:
        """
        SAFE METHOD: Check if a token qualifies for new token bonus
        Returns (bonus_points, status_message)
        """
        try:
            # Quick check based on ranking first (fast path)
            if market_cap_rank and isinstance(market_cap_rank, (int, float)):
                if 500 <= market_cap_rank <= 1500:  # Derive was #800
                    ranking_bonus = 8
                    return ranking_bonus, f"📈 Mid-tier ranking: #{market_cap_rank}"
                elif market_cap_rank > 1500:
                    ranking_bonus = 12
                    return ranking_bonus, f"💎 Low-tier gem: #{market_cap_rank}"
            
            # Check trending status (uses existing free API)
            trending_bonus = await self._check_trending_status(coin_id)
            if trending_bonus > 0:
                return trending_bonus, "🔥 Trending token detected"
                
            # Check for new listing indicators in symbol/name
            if self._has_new_token_indicators(coin_symbol):
                return 5, "🆕 New token indicators detected"
                
        except Exception as e:
            logging.debug(f"New token check error for {coin_id}: {e}")
        
        return 0, ""
    
    async def _check_trending_status(self, coin_id: str) -> int:
        """Check if token is trending (reuses existing logic)"""
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                trending_coins = data.get('coins', [])
                
                for coin in trending_coins:
                    if coin.get('item', {}).get('id') == coin_id:
                        return 10  # Trending bonus
        except Exception as e:
            logging.debug(f"Trending check error: {e}")
        
        return 0
    
    def _has_new_token_indicators(self, coin_symbol: str) -> bool:
        """Check for new token indicators in symbol"""
        if not coin_symbol:
            return False
            
        symbol_lower = coin_symbol.lower()
        
        # Common new token indicators
        new_indicators = ['v2', '2.0', 'new', 'gen2', 'next']
        return any(indicator in symbol_lower for indicator in new_indicators)

# =============================================================================
# VOLUME ANALYSIS BY MARKET CAP CATEGORY
# =============================================================================

class SafeVolumeAnalyzer:
    """Safe volume analysis enhancements"""
    
    def __init__(self):
        # Volume thresholds based on market cap (from v2.2 research)
        self.volume_thresholds = {
            'mega_cap': 1_000_000,      # >$50B
            'large_cap': 500_000,       # $10B-$50B 
            'mid_cap': 100_000,         # $1B-$10B (Derive sweet spot)
            'small_cap': 50_000,        # $100M-$1B
            'micro_cap': 10_000,        # $10M-$100M
            'nano_cap': 1_000           # <$10M
        }
    
    def get_market_cap_category(self, market_cap: float) -> str:
        """Categorize by market cap"""
        if market_cap > 50_000_000_000:
            return 'mega_cap'
        elif market_cap > 10_000_000_000:
            return 'large_cap'
        elif market_cap > 1_000_000_000:
            return 'mid_cap'
        elif market_cap > 100_000_000:
            return 'small_cap'
        elif market_cap > 10_000_000:
            return 'micro_cap'
        else:
            return 'nano_cap'
    
    def get_volume_threshold_bonus(self, coin_data: Dict, current_volume: float) -> Tuple[int, str]:
        """Get volume bonus based on market cap category"""
        try:
            market_cap = float(coin_data.get('market_cap', 0) or 0)
            if market_cap == 0:
                # Estimate from price and volume
                price = float(coin_data.get('price', 0) or 0)
                if price > 0 and current_volume > 0:
                    market_cap = current_volume * 20
            
            if market_cap == 0:
                return 0, ""
            
            category = self.get_market_cap_category(market_cap)
            threshold = self.volume_thresholds[category]
            
            if current_volume >= threshold:
                if category in ['micro_cap', 'nano_cap']:
                    bonus = 15
                    return bonus, f"🚀 Strong volume for {category.replace('_', '-')}"
                elif category == 'small_cap':
                    bonus = 10
                    return bonus, f"📈 Good volume for {category.replace('_', '-')}"
                elif category == 'mid_cap':
                    bonus = 8
                    return bonus, f"✅ Solid volume for {category.replace('_', '-')}"
            else:
                # Penalty for very low volume
                if current_volume < threshold * 0.1:
                    penalty = 10  # Reduced penalty to be safe
                    return -penalty, f"⚠️ Low volume for {category.replace('_', '-')}"
                    
        except Exception as e:
            logging.debug(f"Volume threshold bonus error: {e}")
        
        return 0, ""

# =============================================================================
# DEX TRADING ANALYSIS
# =============================================================================

class SafeDEXAnalyzer:
    """Safe DEX trading analysis"""
    
    def get_dex_trading_bonus(self, distribution_status: str) -> Tuple[int, str]:
        """Bonus for DEX-heavy trading (where new tokens often start)"""
        if not distribution_status:
            return 0, ""
            
        distribution_lower = distribution_status.lower()
        
        # Check for DEX indicators
        dex_indicators = ['dex', 'uniswap', 'aerodrome', 'pancake', 'sushi']
        if any(indicator in distribution_lower for indicator in dex_indicators):
            if 'heavy' in distribution_lower or 'dominance' in distribution_lower:
                bonus = 12
                return bonus, "🔄 DEX-native token (early stage)"
            else:
                bonus = 6
                return bonus, "🔄 DEX trading present"
        
        return 0, ""

# =============================================================================
# PREDICTIVE FOMO ALGORITHM
# =============================================================================

class PredictiveFOMOAnalyzer:
    """
    Advanced forecasting system to catch outliers before they explode
    Focus on LEADING indicators, not lagging ones
    """
    
    def __init__(self):
        # Thresholds calibrated for outlier detection
        self.outlier_market_cap_max = 100_000_000  # $100M max - true outliers
        self.min_volume_threshold = 25_000  # Minimum activity level
        self.accumulation_window_days = 14  # Look back period for patterns
        
        # Pattern recognition weights
        self.pattern_weights = {
            'stealth_accumulation': 30,    # Highest weight - best predictor
            'volume_acceleration': 25,     # Volume trend building
            'wallet_concentration': 20,    # Whale accumulation
            'market_timing': 15,           # Sector/market conditions
            'technical_setup': 10          # Price patterns
        }
    
    async def analyze_predictive_signals(self, coin_data: Dict) -> Tuple[int, str, Dict]:
        """
        Main predictive analysis - returns forecasting score (0-100)
        Higher score = higher probability of future pump
        """
        
        coin_id = coin_data.get('id', '')
        current_price = float(coin_data.get('price', 0) or 0)
        current_volume = float(coin_data.get('volume', 0) or 0)
        market_cap = float(coin_data.get('market_cap', 0) or 0)
        
        # Initialize prediction components
        prediction_score = 0
        signals_detected = []
        analysis_details = {}
        
        # SIGNAL 1: Stealth Accumulation Pattern (30 points max)
        stealth_score, stealth_details = await self.detect_stealth_accumulation(
            coin_id, current_volume, current_price
        )
        prediction_score += stealth_score
        analysis_details['stealth_accumulation'] = stealth_details
        if stealth_score >= 20:
            signals_detected.append("🔍 Stealth Accumulation")
        
        # SIGNAL 2: Volume Acceleration Pattern (25 points max)
        acceleration_score, acceleration_details = await self.detect_volume_acceleration(
            coin_id, current_volume
        )
        prediction_score += acceleration_score
        analysis_details['volume_acceleration'] = acceleration_details
        if acceleration_score >= 15:
            signals_detected.append("📈 Volume Building")
        
        # SIGNAL 3: Wallet Concentration Analysis (20 points max)
        concentration_score, concentration_details = await self.analyze_wallet_concentration(
            coin_id, market_cap
        )
        prediction_score += concentration_score
        analysis_details['wallet_concentration'] = concentration_details
        if concentration_score >= 12:
            signals_detected.append("🐋 Whale Activity")
        
        # SIGNAL 4: Market Timing Factors (15 points max)
        timing_score, timing_details = self.analyze_market_timing(coin_data)
        prediction_score += timing_score
        analysis_details['market_timing'] = timing_details
        if timing_score >= 10:
            signals_detected.append("⏰ Market Timing")
        
        # SIGNAL 5: Technical Setup (10 points max)
        technical_score, technical_details = await self.analyze_technical_setup(
            coin_id, current_price
        )
        prediction_score += technical_score
        analysis_details['technical_setup'] = technical_details
        if technical_score >= 6:
            signals_detected.append("📊 Technical Setup")
        
        # OUTLIER BONUS: Extra points for true unknowns
        outlier_bonus = self.calculate_outlier_bonus(coin_data)
        prediction_score += outlier_bonus
        if outlier_bonus > 0:
            signals_detected.append(f"💎 Outlier Gem (+{outlier_bonus})")
        
        # Generate prediction signal
        prediction_signal = self.generate_prediction_signal(
            prediction_score, signals_detected, market_cap
        )
        
        return min(100, prediction_score), prediction_signal, analysis_details
    
    async def detect_stealth_accumulation(self, coin_id: str, current_volume: float, current_price: float) -> Tuple[int, Dict]:
        """
        MOST IMPORTANT: Detect accumulation BEFORE price moves
        This is the holy grail of prediction
        """
        try:
            # Get 14-day volume and price history
            ohlcv = await fetch_ohlcv_data_ultra_fast(coin_id, days=14)
            
            if not ohlcv or 'total_volumes' not in ohlcv or 'prices' not in ohlcv:
                return 0, {"error": "No historical data"}
            
            volumes = [v[1] for v in ohlcv["total_volumes"]]
            prices = [p[1] for p in ohlcv["prices"]]
            
            if len(volumes) < 7 or len(prices) < 7:
                return 0, {"error": "Insufficient data"}
            
            # Calculate accumulation indicators
            score = 0
            details = {}
            
            # 1. Volume Trend Without Price Movement (KEY PREDICTOR)
            recent_vol_avg = statistics.mean(volumes[-3:])
            older_vol_avg = statistics.mean(volumes[-10:-3])
            vol_growth = (recent_vol_avg / older_vol_avg) if older_vol_avg > 0 else 1
            
            recent_price_change = (prices[-1] - prices[-7]) / prices[-7] * 100
            
            # HIGH SCORE: Volume increasing while price stable/declining
            if vol_growth >= 2.0 and abs(recent_price_change) < 5:
                score += 25  # JACKPOT: Volume up, price flat
                details['pattern'] = "Perfect stealth accumulation"
            elif vol_growth >= 1.5 and abs(recent_price_change) < 10:
                score += 15  # Good accumulation
                details['pattern'] = "Moderate accumulation"
            elif vol_growth >= 1.2 and recent_price_change < 0:
                score += 10  # Buying the dip
                details['pattern'] = "Dip accumulation"
            
            # 2. Consistent Volume Growth (Predictive)
            vol_consistency = self.calculate_trend_consistency(volumes[-7:])
            if vol_consistency > 0.7:  # Steady upward trend
                score += 8
                details['consistency'] = "High volume consistency"
            
            # 3. Volume Spikes During Price Dips (Contrarian buying)
            dip_buying_score = self.detect_dip_buying_pattern(volumes, prices)
            score += dip_buying_score
            if dip_buying_score > 0:
                details['dip_buying'] = f"Contrarian buying detected (+{dip_buying_score})"
            
            details.update({
                'vol_growth': vol_growth,
                'price_change_7d': recent_price_change,
                'current_volume': current_volume,
                'avg_volume': recent_vol_avg
            })
            
            return min(30, score), details
            
        except Exception as e:
            logging.error(f"Stealth accumulation analysis error: {e}")
            return 0, {"error": str(e)}
    
    async def detect_volume_acceleration(self, coin_id: str, current_volume: float) -> Tuple[int, Dict]:
        """
        Detect if volume is ACCELERATING (not just high)
        Acceleration predicts breakouts better than absolute volume
        """
        try:
            ohlcv = await fetch_ohlcv_data_ultra_fast(coin_id, days=21)
            
            if not ohlcv or 'total_volumes' not in ohlcv:
                return 0, {"error": "No volume data"}
            
            volumes = [v[1] for v in ohlcv["total_volumes"]]
            if len(volumes) < 14:
                return 0, {"error": "Insufficient volume data"}
            
            score = 0
            details = {}
            
            # Calculate volume acceleration (rate of change of rate of change)
            week1_avg = statistics.mean(volumes[-7:])      # This week
            week2_avg = statistics.mean(volumes[-14:-7])   # Last week  
            week3_avg = statistics.mean(volumes[-21:-14])  # 2 weeks ago
            
            # Acceleration calculation
            recent_growth = (week1_avg / week2_avg) if week2_avg > 0 else 1
            previous_growth = (week2_avg / week3_avg) if week3_avg > 0 else 1
            acceleration = recent_growth / previous_growth if previous_growth > 0 else 1
            
            # Score based on acceleration magnitude
            if acceleration >= 2.0:  # Volume growth is accelerating fast
                score += 20
                details['pattern'] = "Rapid acceleration"
            elif acceleration >= 1.5:
                score += 12
                details['pattern'] = "Moderate acceleration"
            elif acceleration >= 1.2:
                score += 6
                details['pattern'] = "Mild acceleration"
            
            # Bonus for sustained acceleration
            if recent_growth > 1.3 and previous_growth > 1.2:
                score += 5
                details['sustained'] = True
            
            details.update({
                'acceleration': acceleration,
                'recent_growth': recent_growth,
                'week1_avg': week1_avg,
                'week2_avg': week2_avg
            })
            
            return min(25, score), details
            
        except Exception as e:
            logging.error(f"Volume acceleration analysis error: {e}")
            return 0, {"error": str(e)}
    
    async def analyze_wallet_concentration(self, coin_id: str, market_cap: float) -> Tuple[int, Dict]:
        """
        Analyze wallet distribution for whale accumulation patterns
        High concentration can indicate insider/whale accumulation
        """
        try:
            # Use exchange distribution as proxy for wallet concentration
            ticker_data = await fetch_ticker_data_ultra_fast(coin_id)
            
            if not ticker_data or 'tickers' not in ticker_data:
                return 0, {"error": "No exchange data"}
            
            tickers = ticker_data['tickers']
            if not tickers:
                return 0, {"error": "No ticker data"}
            
            score = 0
            details = {}
            
            # Calculate exchange concentration
            total_volume = sum(float(t.get('converted_volume', {}).get('usd', 0) or 0) for t in tickers)
            if total_volume == 0:
                return 0, {"error": "No volume data"}
            
            # Sort by volume
            exchange_volumes = {}
            for ticker in tickers:
                exchange = ticker.get('market', {}).get('name', 'Unknown')
                volume = float(ticker.get('converted_volume', {}).get('usd', 0) or 0)
                exchange_volumes[exchange] = exchange_volumes.get(exchange, 0) + volume
            
            sorted_exchanges = sorted(exchange_volumes.items(), key=lambda x: x[1], reverse=True)
            
            if sorted_exchanges:
                top_exchange_share = sorted_exchanges[0][1] / total_volume
                
                # DEX concentration often indicates early accumulation
                top_exchange = sorted_exchanges[0][0].lower()
                if any(dex in top_exchange for dex in ['uniswap', 'pancake', 'dex', 'aerodrome']):
                    if 0.6 <= top_exchange_share <= 0.9:  # Sweet spot
                        score += 15
                        details['pattern'] = "DEX accumulation phase"
                    elif top_exchange_share > 0.9:
                        score += 8  # Too concentrated
                        details['pattern'] = "High DEX concentration"
                
                # Multiple smaller exchanges can indicate organic growth
                active_exchanges = len([v for v in exchange_volumes.values() if v > total_volume * 0.05])
                if active_exchanges >= 3 and top_exchange_share < 0.7:
                    score += 10
                    details['pattern'] = "Distributed accumulation"
                
                details.update({
                    'top_exchange': sorted_exchanges[0][0],
                    'top_share': top_exchange_share,
                    'active_exchanges': active_exchanges,
                    'total_volume': total_volume
                })
            
            return min(20, score), details
            
        except Exception as e:
            logging.error(f"Wallet concentration analysis error: {e}")
            return 0, {"error": str(e)}
    
    def analyze_market_timing(self, coin_data: Dict) -> Tuple[int, Dict]:
        """
        Analyze market timing factors that influence pump probability
        """
        score = 0
        details = {}
        
        # Time-based patterns
        now = datetime.now()
        
        # Day of week patterns (from your existing research)
        day_weights = {1: 1.15, 4: 1.15}  # Tuesday, Friday
        if now.weekday() in day_weights:
            score += 5
            details['favorable_day'] = f"{now.strftime('%A')} (historical advantage)"
        
        # Month patterns
        if now.month in [4, 10, 11]:  # April, October, November
            score += 5
            details['favorable_month'] = f"{now.strftime('%B')} (bull season)"
        
        # Market cap category timing
        market_cap = float(coin_data.get('market_cap', 0) or 0)
        if 10_000_000 <= market_cap <= 100_000_000:  # $10M-$100M sweet spot
            score += 5
            details['market_cap_timing'] = "Optimal growth range"
        
        return score, details
    
    async def analyze_technical_setup(self, coin_id: str, current_price: float) -> Tuple[int, Dict]:
        """
        Analyze technical patterns that precede breakouts
        """
        try:
            ohlcv = await fetch_ohlcv_data_ultra_fast(coin_id, days=30)
            
            if not ohlcv or 'prices' not in ohlcv:
                return 0, {"error": "No price data"}
            
            prices = [p[1] for p in ohlcv["prices"]]
            if len(prices) < 20:
                return 0, {"error": "Insufficient price data"}
            
            score = 0
            details = {}
            
            # Support/resistance levels
            recent_high = max(prices[-14:])
            recent_low = min(prices[-14:])
            price_range = (recent_high - recent_low) / recent_low * 100
            
            # Consolidation pattern (low volatility before breakout)
            if 5 <= price_range <= 25:  # Tight consolidation
                score += 6
                details['pattern'] = "Consolidation detected"
            
            # Price position in range
            price_position = (current_price - recent_low) / (recent_high - recent_low)
            if 0.3 <= price_position <= 0.7:  # Middle of range
                score += 2
                details['position'] = "Mid-range (breakout potential)"
            elif price_position > 0.8:  # Near resistance
                score += 4
                details['position'] = "Testing resistance"
            
            details.update({
                'recent_high': recent_high,
                'recent_low': recent_low,
                'price_range_pct': price_range,
                'price_position': price_position
            })
            
            return min(10, score), details
            
        except Exception as e:
            logging.error(f"Technical analysis error: {e}")
            return 0, {"error": str(e)}
    
    def calculate_outlier_bonus(self, coin_data: Dict) -> int:
        """
        Extra points for true outlier characteristics
        """
        bonus = 0
        
        market_cap = float(coin_data.get('market_cap', 0) or 0)
        market_cap_rank = coin_data.get('market_cap_rank', 999999)
        
        # True outlier: Low market cap + high rank number
        if market_cap < 50_000_000 and market_cap_rank > 1000:
            bonus += 15  # Major outlier bonus
        elif market_cap < 100_000_000 and market_cap_rank > 500:
            bonus += 10  # Moderate outlier bonus
        elif market_cap_rank > 300:
            bonus += 5   # Minor outlier bonus
        
        # New token bonus (if detectable)
        age_indicators = ['2024', 'v2', 'new', 'gen2']
        coin_name = coin_data.get('name', '').lower()
        if any(indicator in coin_name for indicator in age_indicators):
            bonus += 5
        
        return bonus
    
    def calculate_trend_consistency(self, values: List[float]) -> float:
        """Calculate how consistently a trend is moving in one direction"""
        if len(values) < 3:
            return 0
        
        differences = [values[i+1] - values[i] for i in range(len(values)-1)]
        positive_diffs = sum(1 for d in differences if d > 0)
        return positive_diffs / len(differences)
    
    def detect_dip_buying_pattern(self, volumes: List[float], prices: List[float]) -> int:
        """Detect if volume spikes occur during price dips (contrarian buying)"""
        if len(volumes) != len(prices) or len(volumes) < 7:
            return 0
        
        score = 0
        for i in range(3, len(prices)-1):  # Look for patterns
            price_change = (prices[i] - prices[i-1]) / prices[i-1] * 100
            volume_change = (volumes[i] - volumes[i-1]) / volumes[i-1] * 100
            
            # Volume spike during price dip
            if price_change < -2 and volume_change > 50:
                score += 3  # Strong contrarian signal
            elif price_change < 0 and volume_change > 20:
                score += 1  # Mild contrarian signal
        
        return min(score, 7)  # Cap the bonus
    
    def generate_prediction_signal(self, score: int, signals: List[str], market_cap: float) -> str:
        """Generate human-readable prediction signal"""
        
        if score >= 80:
            return "🚀 HIGH PUMP PROBABILITY"
        elif score >= 65:
            return "⚡ STRONG ACCUMULATION"
        elif score >= 50:
            return "📈 BUILDING MOMENTUM"
        elif score >= 35:
            return "👀 EARLY SIGNALS"
        elif score >= 20:
            return "🔍 WATCH CLOSELY"
        else:
            return "😴 LOW PREDICTION"

# =============================================================================
# ENHANCED FOMO CALCULATION (SAFE WRAPPER)
# =============================================================================

async def calculate_fomo_status_ultra_fast_enhanced(coin_data):
    """
    ENHANCED version that adds new features while preserving ALL existing functionality
    This is a WRAPPER around your existing v2.1 function
    """
    
    # Import the core enhanced function
    from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
    
    # STEP 1: Run your existing v2.1 calculation (UNCHANGED)
    fomo_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast_v21(coin_data)
    
    # STEP 2: Add safe enhancements (ADDITIONS ONLY)
    coin_id = coin_data.get('id', '')
    coin_symbol = coin_data.get('symbol', '').upper()
    current_volume = float(coin_data.get('volume', 0) or 0)
    market_cap_rank = coin_data.get('market_cap_rank', 999999)
    
    # Store original score for comparison
    original_score = fomo_score
    enhancements = []
    
    try:
        # Enhancement 1: New token detection
        new_token_bonus, new_token_status = await safe_new_token_detector.check_if_new_token(
            coin_id, coin_symbol, market_cap_rank
        )
        fomo_score += new_token_bonus
        if new_token_bonus > 0:
            enhancements.append(f"NewToken:{new_token_bonus:+.1f}")
            logging.info(f"🆕 {new_token_status}")
        
        # Enhancement 2: Volume threshold analysis
        vol_bonus, vol_status = safe_volume_analyzer.get_volume_threshold_bonus(coin_data, current_volume)
        fomo_score += vol_bonus
        if vol_bonus != 0:
            enhancements.append(f"VolThresh:{vol_bonus:+.1f}")
            if vol_status:
                logging.info(f"📊 {vol_status}")
        
        # Enhancement 3: DEX trading bonus
        dex_bonus, dex_status = safe_dex_analyzer.get_dex_trading_bonus(distribution_status)
        fomo_score += dex_bonus
        if dex_bonus > 0:
            enhancements.append(f"DEX:{dex_bonus:+.1f}")
            logging.info(f"🔄 {dex_status}")
        
    except Exception as e:
        logging.warning(f"Enhancement error for {coin_symbol}: {e}")
        # If any enhancement fails, continue with original score
        pass
    
    # STEP 3: Ensure score stays in valid range
    fomo_score = max(0, min(100, fomo_score))
    
    # STEP 4: Enhanced signal types (ADDITIONS ONLY)
    enhanced_signal_type = signal_type  # Start with original
    abs_24h_change = abs(float(coin_data.get('change_24h', 0) or 0))
    
    # Add new signal types for enhanced scores
    if new_token_bonus > 0 and fomo_score >= 70:
        enhanced_signal_type = "🆕 NEW TOKEN BREAKOUT"
    elif new_token_bonus > 0 and fomo_score >= 60:
        enhanced_signal_type = "🆕 New Token Momentum"
    elif fomo_score >= 90 and abs_24h_change < 5.0:
        enhanced_signal_type = "🎯 Stealth Accumulation"
    elif fomo_score >= 85:
        enhanced_signal_type = "🚀 HIGH CONVICTION"
    # Keep all other original signal types...
    
    # STEP 5: Log enhancements if any were applied
    if enhancements:
        total_enhancement = fomo_score - original_score
        logging.info(f"🎯 Safe enhancements for {coin_symbol}: {', '.join(enhancements)} (Total: +{total_enhancement:.1f})")
    
    # STEP 6: Add enhancement info to signal if present
    final_signal = enhanced_signal_type
    if new_token_status and new_token_bonus > 0:
        final_signal += f" ({new_token_status})"
    
    return fomo_score, final_signal, trend_status, distribution_status, volume_spike

# =============================================================================
# MAIN PREDICTIVE FUNCTION
# =============================================================================

async def calculate_predictive_fomo_score(coin_data):
    """
    Enhanced FOMO calculation with predictive elements
    Combines existing reactive scoring with new predictive analysis
    """
    
    # Import the core enhanced function
    from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
    
    # Run existing FOMO analysis
    reactive_score, signal_type, trend_status, distribution_status, volume_spike = await calculate_fomo_status_ultra_fast_v21(coin_data)
    
    # Run new predictive analysis
    predictive_score, prediction_signal, analysis_details = await predictive_analyzer.analyze_predictive_signals(coin_data)
    
    # Combine scores (weighted average)
    reactive_weight = 0.4  # 40% reactive
    predictive_weight = 0.6  # 60% predictive (for forecasting focus)
    
    combined_score = int(reactive_score * reactive_weight + predictive_score * predictive_weight)
    
    # Enhanced signal type
    if predictive_score >= 65:
        enhanced_signal = f"🔮 {prediction_signal}"
    elif predictive_score >= 35:
        enhanced_signal = f"📊 {prediction_signal} | {signal_type}"
    else:
        enhanced_signal = signal_type
    
    # Add prediction confidence
    confidence_level = "High" if predictive_score >= 60 else "Medium" if predictive_score >= 30 else "Low"
    
    return {
        'combined_score': combined_score,
        'enhanced_signal': enhanced_signal,
        'reactive_score': reactive_score,
        'predictive_score': predictive_score,
        'prediction_confidence': confidence_level,
        'trend_status': trend_status,
        'distribution_status': distribution_status,
        'volume_spike': volume_spike,
        'analysis_details': analysis_details
    }

# =============================================================================
# BACKWARD COMPATIBLE WRAPPER
# =============================================================================

async def calculate_fomo_status_ultra_fast_predictive(coin_data):
    """
    Drop-in replacement for existing function with predictive power
    Returns same format as original for compatibility
    """
    result = await calculate_predictive_fomo_score(coin_data)
    
    # Return in original tuple format
    return (
        result['combined_score'],
        result['enhanced_signal'],
        result['trend_status'],
        result['distribution_status'],
        result['volume_spike']
    )

# Initialize pattern analyzers
safe_new_token_detector = NewTokenDetector()
safe_volume_analyzer = SafeVolumeAnalyzer()
safe_dex_analyzer = SafeDEXAnalyzer()
predictive_analyzer = PredictiveFOMOAnalyzer()

# =============================================================================
# TESTING FUNCTIONS
# =============================================================================

async def test_derive_scenario():
    """Test the enhanced analysis with Derive-like data"""
    
    # Simulate Derive's data when it surged
    derive_data = {
        'id': 'derive',
        'symbol': 'DRV',
        'name': 'Derive Protocol',
        'price': 0.028295,
        'volume': 281136,  # The volume when it surged
        'market_cap': 20868400,  # ~$20M market cap
        'market_cap_rank': 800,  # This was key - mid-tier ranking
        'change_1h': 2.5,
        'change_24h': 6.99  # Conservative estimate of the surge
    }
    
    print("🧪 Testing Enhancement on Derive-like scenario...")
    print(f"📊 Input: {derive_data['symbol']} - Rank #{derive_data['market_cap_rank']}, Volume ${derive_data['volume']:,}")
    
    try:
        # Import the core enhanced function
        from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
        
        # Test original v2.1 function
        original_score, original_signal, trend, distribution, vol_spike = await calculate_fomo_status_ultra_fast_v21(derive_data)
        
        print(f"\n📈 ORIGINAL v2.1 Results:")
        print(f"   Score: {original_score}")
        print(f"   Signal: {original_signal}")
        print(f"   Volume Spike: {vol_spike:.1f}x")
        
        # Test enhanced function
        enhanced_score, enhanced_signal, enhanced_trend, enhanced_dist, enhanced_vol = await calculate_fomo_status_ultra_fast_enhanced(derive_data)
        
        print(f"\n🚀 ENHANCED v2.2 Results:")
        print(f"   Score: {enhanced_score}")
        print(f"   Signal: {enhanced_signal}")
        print(f"   Volume Spike: {enhanced_vol:.1f}x")
        
        # Show the difference
        score_improvement = enhanced_score - original_score
        print(f"\n✨ IMPROVEMENT:")
        print(f"   Score Boost: +{score_improvement:.1f} points")
        print(f"   Signal Change: {original_signal} → {enhanced_signal}")
        
        # Determine if this would have been caught
        if enhanced_score >= 75:
            print(f"   🎯 RESULT: Would have been flagged as HIGH OPPORTUNITY!")
        elif enhanced_score >= 60:
            print(f"   🟡 RESULT: Would have been flagged as MODERATE OPPORTUNITY")
        else:
            print(f"   😐 RESULT: Still would have been missed")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def test_predictive_vs_original():
    """Test predictive algorithm against original on sample data"""
    
    # Test coin data
    test_coin = {
        'id': 'test-outlier',
        'symbol': 'TEST',
        'name': 'Test Outlier Coin',
        'price': 0.00234,
        'volume': 150000,
        'market_cap': 25000000,  # $25M outlier
        'market_cap_rank': 850,
        'change_1h': 1.2,
        'change_24h': -1.5  # Slight dip - good for accumulation
    }
    
    print("🧪 TESTING PREDICTIVE vs ORIGINAL")
    print("=" * 50)
    
    try:
        # Import the core enhanced function
        from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
        
        # Test original
        original = await calculate_fomo_status_ultra_fast_v21(test_coin)
        print(f"📈 ORIGINAL: Score={original[0]}, Signal='{original[1]}'")
        
        # Test predictive
        predictive = await calculate_predictive_fomo_score(test_coin)
        print(f"🔮 PREDICTIVE: Score={predictive['combined_score']}, Signal='{predictive['enhanced_signal']}'")
        
        # Show improvement
        improvement = predictive['combined_score'] - original[0]
        print(f"✨ IMPROVEMENT: +{improvement} points")
        
        # Test wrapper (should match predictive)
        wrapper = await calculate_fomo_status_ultra_fast_predictive(test_coin)
        print(f"🔄 WRAPPER: Score={wrapper[0]}, Signal='{wrapper[1]}'")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

# Quick test function you can run immediately
async def quick_test():
    """Quick test you can run right away"""
    await test_derive_scenario()

print("✅ Part 2: Pattern Detection & New Token Analysis loaded!")
print("🎯 Key features:")
print("  - New token detection (ranking-based bonuses)")
print("  - Dynamic volume thresholds by market cap")
print("  - DEX trading detection") 
print("  - Predictive analysis patterns")
print("  - Enhanced signal types for new tokens")
print("🚀 Ready for integration with Part 1!")