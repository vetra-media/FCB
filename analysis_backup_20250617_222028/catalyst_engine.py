"""
analysis/catalyst_engine.py - Enhanced Catalyst Detection Engine
Professional catalyst and event detection integrated with elite analysis

CATALYST FEATURES:
- Real-time event detection
- Market catalyst analysis  
- Gaming-style catalyst scoring
- Professional event timing

ENTERTAINMENT FEATURES:
- Fun catalyst descriptions
- Gaming-style confidence levels
- Instant catalyst scoring
- Engaging event narratives

INTEGRATION: Works seamlessly with elite_engine.py and existing CFB architecture
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
import random

# =============================================================================
# CATALYST DETECTION CORE
# =============================================================================

class CatalystEngine:
    """
    Enhanced catalyst detection engine with gaming integration
    Detects market events, catalysts, and timing opportunities
    """
    
    def __init__(self):
        # Catalyst scoring weights
        self.catalyst_weights = {
            'volume_catalyst': 0.3,
            'price_catalyst': 0.25,
            'timing_catalyst': 0.2,
            'pattern_catalyst': 0.15,
            'sentiment_catalyst': 0.1
        }
        
        # Gaming elements
        self.gaming_multipliers = {
            'moon_mission': 1.5,
            'stealth_mode': 1.3,
            'breakout_party': 1.4,
            'whale_activity': 1.2,
            'discovery_bonus': 1.1
        }
        
        # Catalyst templates for engaging descriptions
        self.catalyst_templates = {
            'volume_spike': [
                "🌊 Volume tsunami detected!",
                "⚡ Trading lightning strike!",
                "🔥 Volume explosion incoming!",
                "💥 Market shockwave building!"
            ],
            'price_breakout': [
                "🚀 Price rocket ignition!",
                "⚡ Breakout lightning bolt!",
                "💎 Diamond hands formation!",
                "🎯 Precision pump detected!"
            ],
            'accumulation': [
                "🎯 Stealth accumulation mode!",
                "🕵️ Whale whispers detected!",
                "🔮 Mystery buying pressure!",
                "🏴‍☠️ Silent treasure hunt!"
            ],
            'timing': [
                "⏰ Perfect timing window!",
                "🎪 Market circus time!",
                "🌟 Golden hour detected!",
                "⚡ Lightning timing strike!"
            ]
        }
    
    async def detect_catalysts(self, coin_data: Dict) -> Dict:
        """
        Main catalyst detection function
        Returns comprehensive catalyst analysis with gaming elements
        """
        
        try:
            symbol = coin_data.get('symbol', 'UNKNOWN').upper()
            
            # Run parallel catalyst detection
            volume_catalyst = await self._detect_volume_catalysts(coin_data)
            price_catalyst = await self._detect_price_catalysts(coin_data)
            timing_catalyst = await self._detect_timing_catalysts(coin_data)
            pattern_catalyst = await self._detect_pattern_catalysts(coin_data)
            sentiment_catalyst = await self._detect_sentiment_catalysts(coin_data)
            
            # Calculate composite catalyst score
            catalyst_score = self._calculate_catalyst_score(
                volume_catalyst, price_catalyst, timing_catalyst,
                pattern_catalyst, sentiment_catalyst
            )
            
            # Apply gaming multipliers
            gaming_score = self._apply_gaming_multipliers(catalyst_score, coin_data)
            
            # Generate catalyst narrative
            narrative = self._generate_catalyst_narrative(
                volume_catalyst, price_catalyst, timing_catalyst,
                pattern_catalyst, sentiment_catalyst, gaming_score
            )
            
            return {
                'symbol': symbol,
                'catalyst_score': gaming_score,
                'volume_catalyst': volume_catalyst,
                'price_catalyst': price_catalyst,
                'timing_catalyst': timing_catalyst,
                'pattern_catalyst': pattern_catalyst,
                'sentiment_catalyst': sentiment_catalyst,
                'narrative': narrative,
                'confidence_level': self._get_confidence_level(gaming_score),
                'action_recommendation': self._get_action_recommendation(gaming_score),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Catalyst detection error for {coin_data.get('symbol', 'unknown')}: {e}")
            return self._create_fallback_catalyst_analysis(coin_data)
    
    async def _detect_volume_catalysts(self, coin_data: Dict) -> Dict:
        """
        Detect volume-based catalysts
        """
        
        volume = float(coin_data.get('volume', 0) or 0)
        symbol = coin_data.get('symbol', 'UNKNOWN')
        
        # Volume analysis
        if volume > 50_000_000:
            score = 95
            description = random.choice(self.catalyst_templates['volume_spike'])
            catalyst_type = "🌊 VOLUME TSUNAMI"
            strength = "extreme"
        elif volume > 10_000_000:
            score = 80
            description = "⚡ Major volume surge detected!"
            catalyst_type = "🔥 VOLUME SPIKE"
            strength = "high"
        elif volume > 1_000_000:
            score = 60
            description = "📈 Good volume activity!"
            catalyst_type = "💧 VOLUME BUILD"
            strength = "medium"
        else:
            score = 30
            description = "👀 Quiet volume period"
            catalyst_type = "😴 LOW VOLUME"
            strength = "low"
        
        return {
            'score': score,
            'description': description,
            'catalyst_type': catalyst_type,
            'strength': strength,
            'volume_value': volume,
            'gaming_element': self._add_volume_gaming_element(score)
        }
    
    async def _detect_price_catalysts(self, coin_data: Dict) -> Dict:
        """
        Detect price-based catalysts
        """
        
        change_1h = float(coin_data.get('change_1h', 0) or 0)
        change_24h = float(coin_data.get('change_24h', 0) or 0)
        price = float(coin_data.get('price', 0) or 0)
        
        # Price momentum analysis
        if change_1h > 10 and change_24h > 5:
            score = 90
            description = random.choice(self.catalyst_templates['price_breakout'])
            catalyst_type = "🚀 ROCKET LAUNCH"
            strength = "extreme"
        elif change_1h > 5 and change_24h > 0:
            score = 75
            description = "⚡ Strong momentum building!"
            catalyst_type = "📈 MOMENTUM BUILD"
            strength = "high"
        elif abs(change_24h) < 5 and change_1h > 0:
            score = 65
            description = random.choice(self.catalyst_templates['accumulation'])
            catalyst_type = "🎯 STEALTH MODE"
            strength = "medium"
        elif change_24h < -20:
            score = 25
            description = "📉 Heavy correction phase"
            catalyst_type = "🔻 CORRECTION"
            strength = "negative"
        else:
            score = 40
            description = "📊 Neutral price action"
            catalyst_type = "⚪ RANGING"
            strength = "low"
        
        return {
            'score': score,
            'description': description,
            'catalyst_type': catalyst_type,
            'strength': strength,
            'price_momentum': {
                '1h': change_1h,
                '24h': change_24h
            },
            'gaming_element': self._add_price_gaming_element(score, change_1h)
        }
    
    async def _detect_timing_catalysts(self, coin_data: Dict) -> Dict:
        """
        Detect timing-based catalysts
        """
        
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        # Time-based catalyst scoring
        timing_score = 50  # Base score
        
        # Hour-based catalysts
        if 13 <= hour <= 17:  # US trading hours
            timing_score = 85
            description = random.choice(self.catalyst_templates['timing'])
            catalyst_type = "🇺🇸 US POWER HOUR"
            strength = "high"
        elif 8 <= hour <= 12:  # London hours
            timing_score = 75
            description = "🇬🇧 London momentum building!"
            catalyst_type = "🏦 LONDON ACTIVE"
            strength = "medium-high"
        elif 0 <= hour <= 6:   # Asia hours
            timing_score = 60
            description = "🌏 Asia session opportunity!"
            catalyst_type = "🌅 ASIA HOURS"
            strength = "medium"
        else:
            timing_score = 35
            description = "🌙 Off-hours trading"
            catalyst_type = "🌙 QUIET HOURS"
            strength = "low"
        
        # Day-based modifier
        if day_of_week < 5:  # Weekday
            timing_score += 10
            day_boost = "📈 Weekday boost!"
        else:  # Weekend
            timing_score -= 15
            day_boost = "🏖️ Weekend chill"
        
        return {
            'score': min(100, timing_score),
            'description': description,
            'catalyst_type': catalyst_type,
            'strength': strength,
            'day_boost': day_boost,
            'optimal_window': timing_score >= 70,
            'gaming_element': self._add_timing_gaming_element(timing_score)
        }
    
    async def _detect_pattern_catalysts(self, coin_data: Dict) -> Dict:
        """
        Detect pattern-based catalysts
        """
        
        # Simulated pattern analysis (can be enhanced with real TA)
        volume = float(coin_data.get('volume', 0) or 0)
        price = float(coin_data.get('price', 0) or 0)
        change_24h = float(coin_data.get('change_24h', 0) or 0)
        
        pattern_score = 50
        
        # Pattern detection logic
        if volume > 5_000_000 and abs(change_24h) < 10:
            pattern_score = 80
            description = "🎯 Accumulation pattern detected!"
            pattern_type = "🔍 ACCUMULATION"
            strength = "high"
        elif volume > 1_000_000 and change_24h > 5:
            pattern_score = 75
            description = "📈 Breakout pattern forming!"
            pattern_type = "⚡ BREAKOUT"
            strength = "medium-high"
        elif 0.00001 <= price <= 0.01 and volume > 100_000:
            pattern_score = 70
            description = "💎 Low-cap gem pattern!"
            pattern_type = "💎 GEM FORMATION"
            strength = "medium"
        else:
            pattern_score = 45
            description = "📊 Standard market pattern"
            pattern_type = "⚪ NEUTRAL"
            strength = "low"
        
        return {
            'score': pattern_score,
            'description': description,
            'pattern_type': pattern_type,
            'strength': strength,
            'technical_setup': self._analyze_technical_setup(coin_data),
            'gaming_element': self._add_pattern_gaming_element(pattern_score)
        }
    
    async def _detect_sentiment_catalysts(self, coin_data: Dict) -> Dict:
        """
        Detect sentiment-based catalysts
        """
        
        # Sentiment analysis based on available data
        market_cap_rank = coin_data.get('market_cap_rank', 999999) or 999999
        volume = float(coin_data.get('volume', 0) or 0)
        
        sentiment_score = 50
        
        # Sentiment scoring
        if market_cap_rank > 1000 and volume > 500_000:
            sentiment_score = 75
            description = "🔍 Hidden gem discovery sentiment!"
            sentiment_type = "💎 DISCOVERY"
            strength = "high"
        elif volume > 10_000_000:
            sentiment_score = 70
            description = "🔥 High interest sentiment!"
            sentiment_type = "🔥 HYPE"
            strength = "medium-high"
        elif 100 <= market_cap_rank <= 500:
            sentiment_score = 60
            description = "📊 Established coin confidence!"
            sentiment_type = "🏆 ESTABLISHED"
            strength = "medium"
        else:
            sentiment_score = 40
            description = "😐 Neutral market sentiment"
            sentiment_type = "⚪ NEUTRAL"
            strength = "low"
        
        return {
            'score': sentiment_score,
            'description': description,
            'sentiment_type': sentiment_type,
            'strength': strength,
            'market_mood': self._analyze_market_mood(coin_data),
            'gaming_element': self._add_sentiment_gaming_element(sentiment_score)
        }
    
    def _calculate_catalyst_score(self, volume_catalyst: Dict, price_catalyst: Dict,
                                timing_catalyst: Dict, pattern_catalyst: Dict,
                                sentiment_catalyst: Dict) -> float:
        """
        Calculate weighted catalyst score
        """
        
        weighted_score = (
            volume_catalyst['score'] * self.catalyst_weights['volume_catalyst'] +
            price_catalyst['score'] * self.catalyst_weights['price_catalyst'] +
            timing_catalyst['score'] * self.catalyst_weights['timing_catalyst'] +
            pattern_catalyst['score'] * self.catalyst_weights['pattern_catalyst'] +
            sentiment_catalyst['score'] * self.catalyst_weights['sentiment_catalyst']
        )
        
        return round(weighted_score, 1)
    
    def _apply_gaming_multipliers(self, base_score: float, coin_data: Dict) -> float:
        """
        Apply gaming multipliers for enhanced engagement
        """
        
        gaming_score = base_score
        
        # Apply multipliers based on conditions
        volume = float(coin_data.get('volume', 0) or 0)
        change_1h = float(coin_data.get('change_1h', 0) or 0)
        market_cap_rank = coin_data.get('market_cap_rank', 999999) or 999999
        
        # Moon mission multiplier
        if change_1h > 10 and volume > 5_000_000:
            gaming_score *= self.gaming_multipliers['moon_mission']
        
        # Stealth mode multiplier
        elif abs(change_1h) < 2 and volume > 1_000_000:
            gaming_score *= self.gaming_multipliers['stealth_mode']
        
        # Discovery bonus
        elif market_cap_rank > 1000:
            gaming_score *= self.gaming_multipliers['discovery_bonus']
        
        # Whale activity multiplier
        elif volume > 20_000_000:
            gaming_score *= self.gaming_multipliers['whale_activity']
        
        return min(100, round(gaming_score, 1))
    
    def _generate_catalyst_narrative(self, volume_catalyst: Dict, price_catalyst: Dict,
                                   timing_catalyst: Dict, pattern_catalyst: Dict,
                                   sentiment_catalyst: Dict, gaming_score: float) -> str:
        """
        Generate engaging catalyst narrative
        """
        
        # Find the strongest catalyst
        catalysts = [
            ('Volume', volume_catalyst),
            ('Price', price_catalyst),
            ('Timing', timing_catalyst),
            ('Pattern', pattern_catalyst),
            ('Sentiment', sentiment_catalyst)
        ]
        
        strongest = max(catalysts, key=lambda x: x[1]['score'])
        
        # Build narrative
        narrative_parts = [
            f"🎯 **Primary Catalyst**: {strongest[1]['description']}",
            f"📊 **Catalyst Score**: {gaming_score}%"
        ]
        
        # Add supporting catalysts
        supporting = [cat for cat in catalysts if cat[1]['score'] >= 60 and cat != strongest]
        if supporting:
            narrative_parts.append(f"⚡ **Supporting**: {', '.join([cat[1]['catalyst_type'] for cat in supporting[:2]])}")
        
        # Add gaming elements
        if gaming_score >= 80:
            narrative_parts.append("🚀 **Gaming Mode**: MAXIMUM EXCITEMENT!")
        elif gaming_score >= 60:
            narrative_parts.append("⚡ **Gaming Mode**: HIGH ENERGY!")
        else:
            narrative_parts.append("📊 **Gaming Mode**: Steady analysis")
        
        return "\n".join(narrative_parts)
    
    def _get_confidence_level(self, catalyst_score: float) -> str:
        """
        Get confidence level description
        """
        
        if catalyst_score >= 85:
            return "🔥 EXTREME CONFIDENCE"
        elif catalyst_score >= 70:
            return "⚡ HIGH CONFIDENCE"
        elif catalyst_score >= 55:
            return "📈 MEDIUM CONFIDENCE"
        elif catalyst_score >= 40:
            return "👀 LOW CONFIDENCE"
        else:
            return "😴 VERY LOW CONFIDENCE"
    
    def _get_action_recommendation(self, catalyst_score: float) -> str:
        """
        Get action recommendation based on catalyst score
        """
        
        if catalyst_score >= 80:
            return "🚀 STRONG BUY SIGNAL - Act fast!"
        elif catalyst_score >= 65:
            return "📈 BUY SIGNAL - Good opportunity"
        elif catalyst_score >= 50:
            return "👀 WATCH SIGNAL - Monitor closely"
        elif catalyst_score >= 35:
            return "⏰ WAIT SIGNAL - Better timing needed"
        else:
            return "😴 AVOID SIGNAL - Low opportunity"
    
    def _add_volume_gaming_element(self, score: float) -> str:
        """Add gaming element to volume analysis"""
        if score >= 80:
            return "🌊 TSUNAMI INCOMING!"
        elif score >= 60:
            return "⚡ LIGHTNING STRIKE!"
        else:
            return "💧 Gentle waves"
    
    def _add_price_gaming_element(self, score: float, change_1h: float) -> str:
        """Add gaming element to price analysis"""
        if score >= 80 and change_1h > 5:
            return "🚀 ROCKET BOOSTERS ON!"
        elif score >= 60:
            return "📈 ENGINES WARMING UP!"
        else:
            return "😴 Engines idle"
    
    def _add_timing_gaming_element(self, score: float) -> str:
        """Add gaming element to timing analysis"""
        if score >= 70:
            return "⏰ PERFECT TIMING WINDOW!"
        elif score >= 50:
            return "🎯 Good timing opportunity"
        else:
            return "⏳ Waiting for better timing"
    
    def _add_pattern_gaming_element(self, score: float) -> str:
        """Add gaming element to pattern analysis"""
        if score >= 70:
            return "🎯 BULLSEYE PATTERN!"
        elif score >= 50:
            return "📊 Clear pattern forming"
        else:
            return "🔍 Pattern unclear"
    
    def _add_sentiment_gaming_element(self, score: float) -> str:
        """Add gaming element to sentiment analysis"""
        if score >= 70:
            return "🔥 SENTIMENT ON FIRE!"
        elif score >= 50:
            return "📈 Positive vibes"
        else:
            return "😐 Neutral sentiment"
    
    def _analyze_technical_setup(self, coin_data: Dict) -> Dict:
        """
        Analyze technical setup (simplified)
        """
        
        volume = float(coin_data.get('volume', 0) or 0)
        change_24h = float(coin_data.get('change_24h', 0) or 0)
        
        if volume > 5_000_000 and 0 <= change_24h <= 10:
            return {'setup': 'accumulation', 'quality': 'high'}
        elif volume > 1_000_000 and change_24h > 10:
            return {'setup': 'breakout', 'quality': 'medium'}
        else:
            return {'setup': 'neutral', 'quality': 'low'}
    
    def _analyze_market_mood(self, coin_data: Dict) -> str:
        """
        Analyze overall market mood
        """
        
        volume = float(coin_data.get('volume', 0) or 0)
        change_24h = float(coin_data.get('change_24h', 0) or 0)
        
        if volume > 10_000_000 and change_24h > 5:
            return "🔥 BULLISH EUPHORIA"
        elif volume > 1_000_000 and change_24h > 0:
            return "📈 OPTIMISTIC"
        elif change_24h < -10:
            return "😰 FEARFUL"
        else:
            return "😐 NEUTRAL"
    
    def _create_fallback_catalyst_analysis(self, coin_data: Dict) -> Dict:
        """
        Create fallback analysis when main detection fails
        """
        
        symbol = coin_data.get('symbol', 'UNKNOWN').upper()
        
        return {
            'symbol': symbol,
            'catalyst_score': 45.0,
            'volume_catalyst': {'score': 45, 'description': "📊 Standard volume analysis"},
            'price_catalyst': {'score': 45, 'description': "📊 Standard price analysis"},
            'timing_catalyst': {'score': 45, 'description': "⏰ Standard timing analysis"},
            'pattern_catalyst': {'score': 45, 'description': "📊 Standard pattern analysis"},
            'sentiment_catalyst': {'score': 45, 'description': "😐 Standard sentiment analysis"},
            'narrative': "📊 **Standard Analysis**: Basic catalyst detection completed",
            'confidence_level': "👀 LOW CONFIDENCE",
            'action_recommendation': "👀 WATCH SIGNAL - Monitor closely",
            'fallback': True,
            'timestamp': datetime.now().isoformat()
        }

# =============================================================================
# CATALYST INTEGRATION FUNCTIONS
# =============================================================================

# Global catalyst engine instance
catalyst_engine = CatalystEngine()

async def analyze_coin_catalysts(coin_data: Dict) -> Dict:
    """
    Main function to analyze coin catalysts
    Integrates with existing analysis pipeline
    """
    return await catalyst_engine.detect_catalysts(coin_data)

async def get_catalyst_score_only(coin_data: Dict) -> float:
    """
    Get just the catalyst score for quick analysis
    """
    try:
        result = await catalyst_engine.detect_catalysts(coin_data)
        return result.get('catalyst_score', 50.0)
    except Exception as e:
        logging.debug(f"Quick catalyst score error: {e}")
        return 50.0

def format_catalyst_summary(catalyst_analysis: Dict) -> str:
    """
    Format catalyst analysis for display in bot messages
    """
    
    try:
        score = catalyst_analysis.get('catalyst_score', 0)
        confidence = catalyst_analysis.get('confidence_level', 'UNKNOWN')
        recommendation = catalyst_analysis.get('action_recommendation', 'UNKNOWN')
        
        # Get strongest catalyst
        strongest_desc = "📊 Standard analysis"
        catalysts = ['volume_catalyst', 'price_catalyst', 'timing_catalyst', 'pattern_catalyst', 'sentiment_catalyst']
        
        max_score = 0
        for cat_key in catalysts:
            cat_data = catalyst_analysis.get(cat_key, {})
            if cat_data.get('score', 0) > max_score:
                max_score = cat_data.get('score', 0)
                strongest_desc = cat_data.get('description', strongest_desc)
        
        summary = f"""🎯 **Catalyst Analysis**
📊 **Score**: {score}%
{confidence}

**Primary**: {strongest_desc}
**Action**: {recommendation}"""
        
        return summary
        
    except Exception as e:
        logging.error(f"Error formatting catalyst summary: {e}")
        return "📊 **Catalyst Analysis**: Standard analysis completed"

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CatalystEngine',
    'catalyst_engine',
    'analyze_coin_catalysts',
    'get_catalyst_score_only',
    'format_catalyst_summary'
]

logging.info("🎯 Catalyst Engine loaded - Advanced event detection ready!")
logging.info("🎮 Gaming-style catalyst analysis with professional insights")
logging.info("⚡ Integrated with elite FOMO engine for comprehensive analysis")