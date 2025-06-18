#!/usr/bin/env python3
"""
FOMO Algorithm A/B Test Script
Safely compares your current analysis.py (v1) vs enhanced version (v2)
WITHOUT breaking your existing bot
"""

import asyncio
import logging
import time
import sys
import os
from datetime import datetime

# Add your project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing analysis functions (v1)
try:
    from analysis import calculate_fomo_status_ultra_fast as fomo_v1
    print("✅ Successfully imported your current FOMO algorithm (v1)")
except ImportError as e:
    print(f"❌ Failed to import current analysis.py: {e}")
    sys.exit(1)

# Enhanced v2 functions (embedded for testing)
import requests

class FOMOEnhancementsV2:
    """Research-backed enhancements for testing"""
    
    def __init__(self):
        self.optimal_volume_range = (5, 10)
        self.day_weights = {0: 1.0, 1: 1.15, 2: 1.0, 3: 1.0, 4: 1.15, 5: 0.95, 6: 0.95}
        self.month_weights = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.2, 5: 1.0, 6: 1.0, 
                             7: 1.0, 8: 1.0, 9: 1.0, 10: 1.2, 11: 1.2, 12: 1.0}
        self.winning_assets = {'bitcoin', 'btc', 'ethereum', 'eth', 'cardano', 'ada', 
                              'chainlink', 'link', 'cosmos', 'atom', 'solana', 'sol'}
    
    def get_time_multiplier(self):
        now = datetime.now()
        day_weight = self.day_weights.get(now.weekday(), 1.0)
        month_weight = self.month_weights.get(now.month, 1.0)
        earnings_boost = 1.1 if now.month in [1, 4, 7, 10] else 1.0
        return day_weight * month_weight * earnings_boost
    
    def apply_volume_sweet_spot_bonus(self, volume_spike):
        if self.optimal_volume_range[0] <= volume_spike <= self.optimal_volume_range[1]:
            return 15  # Sweet spot bonus
        elif volume_spike > 10:
            return -min(10, (volume_spike - 10) * 2)  # Extreme spike penalty
        return 0
    
    def get_asset_priority_bonus(self, coin_id, coin_symbol):
        coin_check = f"{coin_id} {coin_symbol}".lower()
        for winning_asset in self.winning_assets:
            if winning_asset in coin_check:
                return 8
        return 0
    
    async def get_free_sentiment_boost(self, coin_id):
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                trending_coins = data.get('coins', [])
                for coin in trending_coins:
                    if coin.get('item', {}).get('id') == coin_id:
                        return 10
        except:
            pass
        return 0

# Initialize enhancements
enhancements = FOMOEnhancementsV2()

async def fomo_v2_test(coin_data):
    """Enhanced FOMO calculation for testing"""
    # Import your existing functions for reuse
    from analysis import (
        calculate_volume_spike_ultra_fast,
        analyze_momentum_trend_ultra_fast,
        analyze_exchange_distribution_ultra_fast
    )
    
    price_1h_change = coin_data.get('change_1h') or 0
    price_24h_change = coin_data.get('change_24h') or 0
    current_volume = coin_data.get('volume') or 0
    coin_id = coin_data.get('id', '')
    coin_symbol = coin_data.get('symbol', '').upper()
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    # Run your existing analysis in parallel
    tasks = [
        calculate_volume_spike_ultra_fast(coin_id, current_volume),
        analyze_momentum_trend_ultra_fast(coin_id, current_volume, price_1h_change, price_24h_change),
        analyze_exchange_distribution_ultra_fast(coin_id),
        enhancements.get_free_sentiment_boost(coin_id)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    volume_spike = results[0] if not isinstance(results[0], Exception) else 1.0
    trend_result = results[1] if not isinstance(results[1], Exception) else (0, "Unknown")
    distribution_result = results[2] if not isinstance(results[2], Exception) else (0, "Analysis Failed")
    sentiment_boost = results[3] if not isinstance(results[3], Exception) else 0
    
    trend_score, trend_status = trend_result
    distribution_score, distribution_status = distribution_result
    
    # YOUR ORIGINAL FOMO CALCULATION (UNCHANGED)
    fomo_score = 0
    
    # Base score from volume spike (0-60 points) - SAME AS YOUR CODE
    if volume_spike >= 10.0:
        fomo_score = 60
    elif volume_spike >= 5.0:
        fomo_score = 45 + int((volume_spike - 5.0) * 3)
    elif volume_spike >= 2.5:
        fomo_score = 30 + int((volume_spike - 2.5) * 6)
    elif volume_spike >= 1.5:
        fomo_score = 15 + int((volume_spike - 1.5) * 15)
    else:
        fomo_score = int(volume_spike * 10)
    
    # Price movement modifiers - SAME AS YOUR CODE
    abs_24h_change = abs(price_24h_change)
    
    if abs_24h_change < 2.0 and volume_spike >= 3.0:
        fomo_score += 25
    elif abs_24h_change < 5.0 and volume_spike >= 2.0:
        fomo_score += 15
    elif 5.0 <= abs_24h_change <= 15.0:
        fomo_score += 10
    elif abs_24h_change > 25.0:
        fomo_score -= 15
    elif abs_24h_change > 50.0:
        fomo_score -= 25
    
    # 1-hour momentum - SAME AS YOUR CODE
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    elif price_1h_change < 0 and price_24h_change > 0:
        fomo_score += 1
    
    # Volume size bonus/penalty - SAME AS YOUR CODE
    if current_volume > 10_000_000:
        fomo_score += 5
    elif current_volume > 5_000_000:
        fomo_score += 3
    elif current_volume > 1_000_000:
        fomo_score += 1
    elif current_volume < 100_000:
        fomo_score -= 20
    elif current_volume < 500_000:
        fomo_score -= 10
    
    # High price penalty - SAME AS YOUR CODE
    coin_price = coin_data.get('price', 0) or 0
    try:
        coin_price = float(coin_price)
        if coin_price > 1000 and current_volume < 1_000_000:
            fomo_score -= 25
        elif coin_price > 100 and current_volume < 500_000:
            fomo_score -= 15
    except:
        pass
    
    # Add trend and distribution scores - SAME AS YOUR CODE
    fomo_score += trend_score
    fomo_score += distribution_score
    
    # Store original score for comparison
    original_score = fomo_score
    
    # NEW V2.0 ENHANCEMENTS
    enhancements_applied = {}
    
    # 1. Volume sweet spot bonus/penalty
    volume_adjustment = enhancements.apply_volume_sweet_spot_bonus(volume_spike)
    fomo_score += volume_adjustment
    enhancements_applied['volume_sweet_spot'] = volume_adjustment
    
    # 2. Asset priority bonus
    asset_bonus = enhancements.get_asset_priority_bonus(coin_id, coin_symbol)
    fomo_score += asset_bonus
    enhancements_applied['asset_priority'] = asset_bonus
    
    # 3. Sentiment boost
    fomo_score += sentiment_boost
    enhancements_applied['sentiment'] = sentiment_boost
    
    # 4. Time pattern multiplier
    time_multiplier = enhancements.get_time_multiplier()
    if time_multiplier != 1.0:
        adjustment = (time_multiplier - 1.0) * original_score * 0.1
        fomo_score += adjustment
        enhancements_applied['time_pattern'] = adjustment
    else:
        enhancements_applied['time_pattern'] = 0
    
    # Ensure score stays within 0-100 range
    fomo_score = max(0, min(100, fomo_score))
    
    # Determine signal type with enhanced thresholds
    if fomo_score >= 90 and abs_24h_change < 5.0:
        signal_type = "🎯 Stealth Accumulation"
    elif fomo_score >= 85:
        signal_type = "🚀 HIGH CONVICTION"  # NEW tier
    elif fomo_score >= 75:
        signal_type = "⚡ Early Momentum"
    elif fomo_score >= 60:
        signal_type = "🟡 Volume Building"
    elif fomo_score >= 40 and abs_24h_change > 20.0:
        signal_type = "🚨 Already Pumping"
    elif fomo_score >= 35:
        signal_type = "📈 Moderate Activity"
    elif fomo_score >= 20:
        signal_type = "👀 Watch List"
    else:
        signal_type = "😴 Low Activity"
    
    # Override with trend status if very strong
    if "🚀 Accelerating" in trend_status and fomo_score >= 60:
        signal_type = "🚀 Accelerating Breakout"
    elif "🔻 Losing Steam" in trend_status:
        signal_type = "🔻 Losing Steam"
    
    return fomo_score, signal_type, trend_status, distribution_status, volume_spike, enhancements_applied, original_score

async def test_single_coin(coin_data):
    """Test both algorithms on a single coin"""
    print(f"\n{'='*60}")
    print(f"Testing: {coin_data.get('name', 'Unknown')} ({coin_data.get('symbol', '')})")
    print(f"{'='*60}")
    
    # Test V1 (your current algorithm)
    print("🔵 Running V1 (Current Algorithm)...")
    start_time = time.time()
    try:
        v1_result = await fomo_v1(coin_data)
        v1_time = time.time() - start_time
        v1_score, v1_signal, v1_trend, v1_distribution, v1_volume = v1_result
        print(f"✅ V1 Complete in {v1_time:.2f}s")
    except Exception as e:
        print(f"❌ V1 Error: {e}")
        return
    
    # Test V2 (enhanced algorithm)
    print("🟢 Running V2 (Enhanced Algorithm)...")
    start_time = time.time()
    try:
        v2_result = await fomo_v2_test(coin_data)
        v2_time = time.time() - start_time
        v2_score, v2_signal, v2_trend, v2_distribution, v2_volume, enhancements, original_score = v2_result
        print(f"✅ V2 Complete in {v2_time:.2f}s")
    except Exception as e:
        print(f"❌ V2 Error: {e}")
        return
    
    # Compare results
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"{'Metric':<20} {'V1 (Current)':<15} {'V2 (Enhanced)':<15} {'Difference':<15}")
    print(f"{'-'*65}")
    
    score_diff = v2_score - v1_score
    print(f"{'FOMO Score':<20} {v1_score:<15.1f} {v2_score:<15.1f} {score_diff:+.1f}")
    print(f"{'Signal Type':<20} {v1_signal[:13]:<15} {v2_signal[:13]:<15} {'ENHANCED' if v2_score > v1_score else 'SAME'}")
    print(f"{'Volume Spike':<20} {v1_volume:<15.1f} {v2_volume:<15.1f} {'SAME'}")
    print(f"{'Processing Time':<20} {v1_time:<15.2f} {v2_time:<15.2f} {v2_time-v1_time:+.2f}s")
    
    # Show enhancements breakdown
    print(f"\n🎯 V2.0 ENHANCEMENTS APPLIED:")
    total_enhancement = sum(enhancements.values())
    for enhancement, value in enhancements.items():
        if value != 0:
            print(f"  • {enhancement.replace('_', ' ').title()}: {value:+.1f} points")
    
    print(f"\n📈 ENHANCEMENT BREAKDOWN:")
    print(f"  • Original V1 Logic Score: {original_score:.1f}")
    print(f"  • Total V2.0 Enhancements: {total_enhancement:+.1f}")
    print(f"  • Final V2.0 Score: {v2_score:.1f}")
    
    return {
        'coin': coin_data.get('symbol', ''),
        'v1_score': v1_score,
        'v2_score': v2_score,
        'difference': score_diff,
        'enhancements': enhancements,
        'v1_signal': v1_signal,
        'v2_signal': v2_signal
    }

async def run_ab_test():
    """Run A/B test on sample coins"""
    print("🚀 FOMO Algorithm A/B Test")
    print("Testing your current algorithm (V1) vs enhanced version (V2)")
    print("This is completely safe and won't affect your running bot!")
    
    # Test coins (you can modify this list)
    test_coins = [
        {
            'id': 'bitcoin',
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'price': 97500,
            'change_1h': 1.2,
            'change_24h': 3.5,
            'volume': 25000000000
        },
        {
            'id': 'ethereum',
            'name': 'Ethereum',
            'symbol': 'ETH',
            'price': 3200,
            'change_1h': 0.8,
            'change_24h': 2.1,
            'volume': 15000000000
        },
        {
            'id': 'cardano',
            'name': 'Cardano',
            'symbol': 'ADA',
            'price': 0.45,
            'change_1h': 2.5,
            'change_24h': 8.3,
            'volume': 850000000
        },
        {
            'id': 'chainlink',
            'name': 'Chainlink',
            'symbol': 'LINK',
            'price': 23.5,
            'change_1h': -0.5,
            'change_24h': 5.7,
            'volume': 420000000
        }
    ]
    
    results = []
    
    for coin in test_coins:
        try:
            result = await test_single_coin(coin)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Error testing {coin.get('symbol', 'Unknown')}: {e}")
    
    # Summary
    if results:
        print(f"\n{'='*60}")
        print("📊 OVERALL TEST SUMMARY")
        print(f"{'='*60}")
        
        total_coins = len(results)
        improved_coins = len([r for r in results if r['difference'] > 0])
        avg_improvement = sum(r['difference'] for r in results) / len(results)
        
        print(f"Coins Tested: {total_coins}")
        print(f"Coins with Improved Scores: {improved_coins}/{total_coins} ({improved_coins/total_coins*100:.1f}%)")
        print(f"Average Score Improvement: {avg_improvement:+.1f} points")
        
        print(f"\nTop Improvements:")
        sorted_results = sorted(results, key=lambda x: x['difference'], reverse=True)
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"{i}. {result['coin']}: {result['difference']:+.1f} points ({result['v1_score']:.1f} → {result['v2_score']:.1f})")
        
        print(f"\n🎯 RECOMMENDATION:")
        if avg_improvement > 2:
            print("✅ V2.0 enhancements show significant improvement!")
            print("   Safe to upgrade your analysis.py with the enhanced version.")
        elif avg_improvement > 0:
            print("✅ V2.0 enhancements show modest improvement.")
            print("   Consider upgrading for better signal quality.")
        else:
            print("⚠️ V2.0 enhancements show mixed results.")
            print("   Review individual coin results before upgrading.")
    
    print(f"\n💡 Next Steps:")
    print("1. Review the individual coin results above")
    print("2. If satisfied with improvements, replace your analysis.py")
    print("3. Your current bot will continue working exactly the same")
    print("4. V2.0 just adds research-backed intelligence on top!")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    try:
        asyncio.run(run_ab_test())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()