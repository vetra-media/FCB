# analysis_new/elite_analyzer.py
"""
Elite FOMO Analyzer - Production Ready
Replaces all 5 legacy analysis engines with one proven algorithm
Based on top 1% crypto trader behaviors
"""

import asyncio
import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import math

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Clean data structure for analysis results"""
    score: float
    signal: str
    analysis: str
    breakdown: Dict[str, float]
    timestamp: datetime
    confidence: str
    risk_level: str

class EliteFOMOAnalyzer:
    """
    Production-ready FOMO analyzer that mimics top 1% trader behaviors
    """
    
    def __init__(self):
        # Market timing windows (UTC) - based on historical volatility patterns
        self.high_prob_hours = [13, 14, 15, 20, 21, 22]  # US open + Asia evening
        self.chop_hours = [2, 3, 4, 5, 6, 7]  # Low probability dead hours
        
        # Volume thresholds by market cap (smart money requirements)
        self.volume_thresholds = {
            'mega': (1_000_000_000, 50_000_000),    # >$1B mcap needs >$50M volume
            'large': (100_000_000, 10_000_000),     # >$100M mcap needs >$10M volume
            'mid': (10_000_000, 2_000_000),         # >$10M mcap needs >$2M volume
            'small': (1_000_000, 500_000),          # >$1M mcap needs >$500K volume
            'micro': (0, 100_000)                   # <$1M mcap needs >$100K volume
        }
        
        # Performance tracking
        self.analysis_count = 0
        self.last_reset = datetime.utcnow()

    async def analyze(self, coin_data: Dict) -> AnalysisResult:
        """Main analysis entry point"""
        try:
            self.analysis_count += 1
            
            if not self._validate_input(coin_data):
                return self._create_error_result("Invalid input data")
            
            metrics = self._extract_metrics(coin_data)
            score, breakdown = await self._calculate_elite_score(metrics)
            signal, analysis, confidence, risk_level = self._generate_trading_signal(score, breakdown, metrics)
            
            result = AnalysisResult(
                score=score,
                signal=signal,
                analysis=analysis,
                breakdown=breakdown,
                timestamp=datetime.utcnow(),
                confidence=confidence,
                risk_level=risk_level
            )
            
            logger.info(f"Analysis complete: {coin_data.get('symbol', 'UNKNOWN')} scored {score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return self._create_error_result(f"Analysis error: {str(e)}")

    def _validate_input(self, coin_data: Dict) -> bool:
        """Validate required fields exist and are reasonable"""
        required_fields = ['price', 'volume_24h', 'market_cap']
        
        for field in required_fields:
            if field not in coin_data:
                return False
            try:
                value = float(coin_data[field])
                if value < 0 or math.isnan(value) or math.isinf(value):
                    return False
            except (ValueError, TypeError):
                return False
        return True

    def _extract_metrics(self, coin_data: Dict) -> Dict:
        """Extract and clean all required metrics"""
        return {
            'price': float(coin_data.get('price', 0)),
            'volume_24h': float(coin_data.get('volume_24h', 0)),
            'market_cap': float(coin_data.get('market_cap', 0)),
            'change_1h': float(coin_data.get('price_change_percentage_1h', 0)),
            'change_24h': float(coin_data.get('price_change_percentage_24h', 0)),
            'change_7d': float(coin_data.get('price_change_percentage_7d', 0)),
            'volume_change': float(coin_data.get('volume_change_24h', 0)),
            'symbol': coin_data.get('symbol', 'UNKNOWN')
        }

    async def _calculate_elite_score(self, metrics: Dict) -> Tuple[float, Dict]:
        """Core elite scoring algorithm"""
        breakdown = {
            'order_flow': 0,
            'timing': 0,
            'risk_reward': 0,
            'sentiment_momentum': 0,
            'liquidity_depth': 0
        }
        
        breakdown['order_flow'] = self._analyze_order_flow(
            metrics['volume_24h'], metrics['volume_change'], 
            metrics['change_1h'], metrics['change_24h']
        )
        
        breakdown['timing'] = self._analyze_timing()
        
        breakdown['risk_reward'] = self._analyze_risk_reward(
            metrics['change_1h'], metrics['change_24h'], 
            metrics['change_7d'], metrics['price']
        )
        
        breakdown['sentiment_momentum'] = self._analyze_sentiment_momentum(
            metrics['change_1h'], metrics['change_24h'], metrics['volume_change']
        )
        
        breakdown['liquidity_depth'] = self._analyze_liquidity_depth(
            metrics['market_cap'], metrics['volume_24h'], metrics['price']
        )
        
        total_score = sum(breakdown.values())
        return min(100, max(0, total_score)), breakdown

    def _analyze_order_flow(self, volume_24h: float, volume_change: float, 
                           change_1h: float, change_24h: float) -> float:
        """Smart money and institutional flow detection"""
        score = 0
        
        if volume_change > 200 and change_1h > 0:
            score += 15
        elif volume_change > 100 and change_1h > 2:
            score += 12
        elif volume_change > 50 and change_1h > 1:
            score += 8
        
        if change_24h != 0 and volume_24h > 1_000_000:
            volume_efficiency = volume_24h / abs(change_24h)
            if volume_efficiency > 500_000:
                score += 10
            elif volume_efficiency > 100_000:
                score += 6
            elif volume_efficiency > 50_000:
                score += 3
        
        return min(25, score)

    def _analyze_timing(self) -> float:
        """Volatility window and timing optimization"""
        current_hour = datetime.utcnow().hour
        
        if current_hour in self.chop_hours:
            return 0
        elif current_hour in self.high_prob_hours:
            return 20
        else:
            return 10

    def _analyze_risk_reward(self, change_1h: float, change_24h: float, 
                           change_7d: float, price: float) -> float:
        """Risk/reward and probability analysis"""
        score = 0
        
        if change_1h > 3 and change_24h > 5 and change_7d > 0:
            score += 25
        elif change_1h > 1 and change_24h > 0 and change_7d < -10:
            score += 20
        elif change_1h > 0.5 and change_24h < 2:
            score += 15
        elif change_1h > 0 and change_24h > 0:
            score += 10
        
        if 0.000001 <= price <= 0.0001:
            score += 5
        elif 0.01 <= price <= 1:
            score += 3
        
        return min(25, score)

    def _analyze_sentiment_momentum(self, change_1h: float, change_24h: float, 
                                  volume_change: float) -> float:
        """Early sentiment detection before mainstream FOMO"""
        score = 0
        
        if 0.5 <= change_1h <= 5 and volume_change > 50:
            score += 20
        elif change_1h > 10:
            score += 5
        elif change_1h > 5:
            score += 12
        elif change_1h > 0:
            score += 8
        
        if change_1h > 2 and change_24h < 0:
            score += 8
        
        return min(20, score)

    def _analyze_liquidity_depth(self, market_cap: float, volume_24h: float, 
                               price: float) -> float:
        """Liquidity and exit safety analysis"""
        for category, (min_cap, min_volume) in self.volume_thresholds.items():
            if market_cap >= min_cap:
                if volume_24h >= min_volume:
                    return 10
                elif volume_24h >= min_volume * 0.5:
                    return 6
                elif volume_24h >= min_volume * 0.25:
                    return 3
                else:
                    return 1
        return 5

    def _generate_trading_signal(self, score: float, breakdown: Dict, 
                               metrics: Dict) -> Tuple[str, str, str, str]:
        """Generate trading signal, analysis, confidence, and risk assessment"""
        
        if score >= 80:
            signal = "🚀 ELITE SETUP"
            confidence = "HIGH"
            risk_level = "MEDIUM"
        elif score >= 65:
            signal = "📈 STRONG SETUP"
            confidence = "GOOD"
            risk_level = "MEDIUM"
        elif score >= 50:
            signal = "👀 MODERATE SETUP"
            confidence = "MODERATE"
            risk_level = "MEDIUM-HIGH"
        elif score >= 35:
            signal = "⚠️ WEAK SETUP"
            confidence = "LOW"
            risk_level = "HIGH"
        else:
            signal = "❌ AVOID"
            confidence = "VERY LOW"
            risk_level = "VERY HIGH"
        
        analysis_parts = []
        
        if breakdown['order_flow'] >= 15:
            analysis_parts.append("Strong institutional flow")
        elif breakdown['order_flow'] >= 8:
            analysis_parts.append("Moderate volume interest")
        
        if breakdown['timing'] == 20:
            analysis_parts.append("Optimal timing window")
        elif breakdown['timing'] == 0:
            analysis_parts.append("Poor timing (avoid)")
        
        if breakdown['risk_reward'] >= 20:
            analysis_parts.append("Excellent R/R setup")
        elif breakdown['risk_reward'] >= 15:
            analysis_parts.append("Good R/R potential")
        
        if breakdown['sentiment_momentum'] >= 15:
            analysis_parts.append("Early momentum phase")
        elif breakdown['sentiment_momentum'] <= 8:
            analysis_parts.append("Late entry risk")
        
        if breakdown['liquidity_depth'] <= 3:
            analysis_parts.append("⚠️ Liquidity risk")
        
        price_str = f"${metrics['price']:.6f}".rstrip('0').rstrip('.')
        volume_str = f"${metrics['volume_24h']:,.0f}"
        analysis_parts.append(f"Price: {price_str}")
        analysis_parts.append(f"Volume: {volume_str}")
        
        analysis = " | ".join(analysis_parts)
        
        return signal, analysis, confidence, risk_level

    def _create_error_result(self, error_msg: str) -> AnalysisResult:
        """Create error result for failed analysis"""
        return AnalysisResult(
            score=0,
            signal="❌ ERROR",
            analysis=error_msg,
            breakdown={},
            timestamp=datetime.utcnow(),
            confidence="NONE",
            risk_level="UNKNOWN"
        )

    def get_stats(self) -> Dict:
        """Get analyzer performance statistics"""
        uptime = datetime.utcnow() - self.last_reset
        return {
            'total_analyses': self.analysis_count,
            'uptime_hours': uptime.total_seconds() / 3600,
            'analyses_per_hour': self.analysis_count / max(1, uptime.total_seconds() / 3600),
            'last_reset': self.last_reset.isoformat()
        }


def create_analyzer() -> EliteFOMOAnalyzer:
    """Factory function to create analyzer instance"""
    return EliteFOMOAnalyzer()


async def test_analyzer():
    """Test the analyzer with sample data"""
    analyzer = create_analyzer()
    
    test_case = {
        'symbol': 'TEST1',
        'price': 0.0025,
        'volume_24h': 5_000_000,
        'market_cap': 25_000_000,
        'price_change_percentage_1h': 2.5,
        'price_change_percentage_24h': 8.2,
        'price_change_percentage_7d': -5.1,
        'volume_change_24h': 150.5
    }
    
    print(f"\n=== Elite Analyzer Test ===")
    result = await analyzer.analyze(test_case)
    print(f"Score: {result.score:.1f}/100")
    print(f"Signal: {result.signal}")
    print(f"Analysis: {result.analysis}")
    print(f"Confidence: {result.confidence}")
    print(f"Risk Level: {result.risk_level}")


if __name__ == "__main__":
    asyncio.run(test_analyzer())
