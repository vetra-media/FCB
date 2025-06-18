"""
analysis/legacy.py - Preserved Original Functions
Part 3 of 4: All original functions preserved for backward compatibility

UNCHANGED FUNCTIONS:
- All sync fallback functions
- Original calculate_fomo_status()
- Original momentum/distribution analysis
- Original volume spike calculations
- All function signatures preserved
"""

import statistics 
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from api_client import (
    fetch_ohlcv_data_ultra_fast, fetch_ticker_data_ultra_fast,
    fetch_ohlcv_data, rate_limiter
)

# =============================================================================
# FALLBACK SYNC ANALYSIS FUNCTIONS (UNCHANGED)
# =============================================================================

def analyze_exchange_distribution(coin_id):
    """Sync fallback for exchange distribution analysis"""
    return 0, "Sync analysis not implemented - use ultra_fast version"

def analyze_momentum_trend(coin_id, current_volume, current_1h_change, current_24h_change):
    """Sync fallback for momentum trend analysis - UNCHANGED"""
    try:
        ohlcv = fetch_ohlcv_data(coin_id, days=7)
        if not ohlcv or 'total_volumes' not in ohlcv or 'prices' not in ohlcv:
            return 0, "Unknown"
        
        volumes = [v[1] for v in ohlcv["total_volumes"]]
        prices = [p[1] for p in ohlcv["prices"]]
        
        if len(volumes) < 4 or len(prices) < 4:
            return 0, "Insufficient Data"
        
        # Calculate volume trend (last 3 days vs previous 3 days)
        recent_vol_avg = sum(volumes[-3:]) / 3
        older_vol_avg = sum(volumes[-6:-3]) / 3 if len(volumes) >= 6 else sum(volumes[:-3]) / len(volumes[:-3])
        volume_trend = recent_vol_avg / older_vol_avg if older_vol_avg > 0 else 1.0
        
        # Calculate price momentum acceleration
        price_changes = []
        for i in range(1, len(prices)):
            change = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
            price_changes.append(change)
        
        if len(price_changes) >= 3:
            recent_momentum = sum(price_changes[-2:]) / 2
            older_momentum = sum(price_changes[-4:-2]) / 2 if len(price_changes) >= 4 else price_changes[0]
            momentum_acceleration = recent_momentum - older_momentum
        else:
            momentum_acceleration = 0
        
        # Calculate trend score (-15 to +15 points)
        trend_score = 0
        trend_status = "Stable"
        
        # Volume trend analysis
        if volume_trend > 2.0:
            trend_score += 8
            trend_status = "🚀 Accelerating"
        elif volume_trend > 1.3:
            trend_score += 4
            trend_status = "📈 Building"
        elif volume_trend < 0.7:
            trend_score -= 8
            trend_status = "📉 Declining"
        elif volume_trend < 0.9:
            trend_score -= 4
            trend_status = "⚠️ Weakening"
        
        # Momentum acceleration analysis
        if momentum_acceleration > 3.0:
            trend_score += 7
            if "Accelerating" not in trend_status:
                trend_status = "🚀 Momentum Building"
        elif momentum_acceleration > 1.0:
            trend_score += 3
        elif momentum_acceleration < -3.0:
            trend_score -= 7
            trend_status = "🔻 Losing Steam"
        elif momentum_acceleration < -1.0:
            trend_score -= 3
        
        # Current momentum vs recent trend
        if current_1h_change > 2.0 and momentum_acceleration > 0:
            trend_score += 5
        elif current_1h_change < -2.0 and momentum_acceleration < 0:
            trend_score -= 5
        
        return min(15, max(-15, trend_score)), trend_status
        
    except Exception as e:
        logging.debug(f"Sync momentum analysis error: {e}")
        return 0, "Error"

def calculate_real_volume_spike(coin_id, current_volume):
    """Sync fallback for volume spike calculation - UNCHANGED"""
    try:
        ohlcv = fetch_ohlcv_data(coin_id)
        if not ohlcv or 'total_volumes' not in ohlcv:
            return 1.0
        volumes = [v[1] for v in ohlcv["total_volumes"]]
        if len(volumes) < 3:
            return 1.0
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[0]
        volume_spike = current_volume / avg_volume if avg_volume > 0 else 1.0
        return volume_spike
    except Exception as e:
        logging.debug(f"Volume spike calculation error: {e}")
        return 1.0

def calculate_fomo_status(coin_data, volume_spike=None):
    """Standard FOMO calculation with sync functions - UNCHANGED"""
    price_1h_change = coin_data.get('change_1h') or 0
    price_24h_change = coin_data.get('change_24h') or 0
    current_volume = coin_data.get('volume') or 0
    coin_id = coin_data.get('id', '')
    
    logging.info(f"Starting FOMO calculation for {coin_id}")
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    # Calculate volume spike if not provided
    if volume_spike is None:
        volume_spike = calculate_real_volume_spike(coin_id, current_volume)
    
    # Analyze momentum trend
    logging.info(f"Analyzing momentum trend for {coin_id}")
    trend_score, trend_status = analyze_momentum_trend(coin_id, current_volume, price_1h_change, price_24h_change)
    logging.info(f"Trend analysis complete: {trend_status} (Score: {trend_score})")
    
    # Analyze exchange distribution
    logging.info(f"Analyzing exchange distribution for {coin_id}")
    distribution_score, distribution_status = analyze_exchange_distribution(coin_id)
    logging.info(f"Exchange analysis complete: {distribution_status} (Score: {distribution_score})")
    
    fomo_score = 0
    signal_type = "No Signal"
    
    # Base score from volume spike (0-60 points)
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
    
    # Price movement modifiers
    abs_24h_change = abs(price_24h_change)
    
    if abs_24h_change < 2.0 and volume_spike >= 3.0:
        fomo_score += 25  # Stealth accumulation bonus
    elif abs_24h_change < 5.0 and volume_spike >= 2.0:
        fomo_score += 15  # Building pressure
    elif 5.0 <= abs_24h_change <= 15.0:
        fomo_score += 10  # Early momentum
    elif abs_24h_change > 25.0:
        fomo_score -= 15  # Already pumped penalty
    elif abs_24h_change > 50.0:
        fomo_score -= 25  # Major pump penalty
    
    # 1-hour momentum bonus/penalty
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    elif price_1h_change < 0 and price_24h_change > 0:
        fomo_score += 1
    
    # Volume size bonus/penalty
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
    
    # High price coin penalty
    coin_price = coin_data.get('price', 0) or 0
    try:
        coin_price = float(coin_price)
        if coin_price > 1000 and current_volume < 1_000_000:
            fomo_score -= 25
        elif coin_price > 100 and current_volume < 500_000:
            fomo_score -= 15
    except:
        pass
    
    # Add momentum trend score and exchange distribution score
    fomo_score += trend_score
    fomo_score += distribution_score
    
    # Ensure score stays within 0-100 range
    fomo_score = max(0, min(100, fomo_score))
    
    # Determine signal type
    if fomo_score >= 85 and abs_24h_change < 5.0:
        signal_type = "🎯 Stealth Accumulation"
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
    
    # Override signal type with trend status if very strong
    if "🚀 Accelerating" in trend_status and fomo_score >= 60:
        signal_type = "🚀 Accelerating Breakout"
    elif "🔻 Losing Steam" in trend_status:
        signal_type = "🔻 Losing Steam"
    
    return fomo_score, signal_type, trend_status, distribution_status

# =============================================================================
# ORIGINAL ASYNC HELPER FUNCTIONS (PRESERVED)
# =============================================================================

async def calculate_volume_spike_ultra_fast_original(coin_id, current_volume):
    """Original volume spike calculation - UNCHANGED"""
    ohlcv = await fetch_ohlcv_data_ultra_fast(coin_id)
    if not ohlcv or 'total_volumes' not in ohlcv:
        return 1.0
    
    volumes = [v[1] for v in ohlcv["total_volumes"]]
    if len(volumes) < 3:
        return 1.0
    
    # Use last 7 days average excluding today (same as original)
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[0]
    volume_spike = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    return volume_spike

async def analyze_momentum_trend_ultra_fast_original(coin_id, current_volume, current_1h_change, current_24h_change):
    """Ultra-fast momentum analysis - ORIGINAL VERSION"""
    ohlcv = await fetch_ohlcv_data_ultra_fast(coin_id, days=7)
    if not ohlcv or 'total_volumes' not in ohlcv or 'prices' not in ohlcv:
        return 0, "Data Unavailable"
    
    volumes = [v[1] for v in ohlcv["total_volumes"]]
    prices = [p[1] for p in ohlcv["prices"]]
    
    if len(volumes) < 4 or len(prices) < 4:
        return 0, "Insufficient Data"
    
    # Calculate volume trend (last 3 days vs previous 3 days)
    recent_vol_avg = sum(volumes[-3:]) / 3
    older_vol_avg = sum(volumes[-6:-3]) / 3 if len(volumes) >= 6 else sum(volumes[:-3]) / len(volumes[:-3])
    volume_trend = recent_vol_avg / older_vol_avg if older_vol_avg > 0 else 1.0
    
    # Calculate price momentum acceleration
    price_changes = []
    for i in range(1, len(prices)):
        change = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
        price_changes.append(change)
    
    if len(price_changes) >= 3:
        recent_momentum = sum(price_changes[-2:]) / 2
        older_momentum = sum(price_changes[-4:-2]) / 2 if len(price_changes) >= 4 else price_changes[0]
        momentum_acceleration = recent_momentum - older_momentum
    else:
        momentum_acceleration = 0
    
    # Calculate trend score (-15 to +15 points)
    trend_score = 0
    trend_status = "Stable"
    
    if volume_trend > 2.0:
        trend_score += 8
        trend_status = "🚀 Accelerating"
    elif volume_trend > 1.3:
        trend_score += 4
        trend_status = "📈 Building"
    elif volume_trend < 0.7:
        trend_score -= 8
        trend_status = "📉 Declining"
    elif volume_trend < 0.9:
        trend_score -= 4
        trend_status = "⚠️ Weakening"
    
    if momentum_acceleration > 3.0:
        trend_score += 7
        if "Accelerating" not in trend_status:
            trend_status = "🚀 Momentum Building"
    elif momentum_acceleration > 1.0:
        trend_score += 3
    elif momentum_acceleration < -3.0:
        trend_score -= 7
        trend_status = "🔻 Losing Steam"
    elif momentum_acceleration < -1.0:
        trend_score -= 3
    
    if current_1h_change > 2.0 and momentum_acceleration > 0:
        trend_score += 5
    elif current_1h_change < -2.0 and momentum_acceleration < 0:
        trend_score -= 5
    
    return min(15, max(-15, trend_score)), trend_status

async def analyze_exchange_distribution_ultra_fast_original(coin_id):
    """Ultra-fast exchange distribution analysis - ORIGINAL VERSION"""
    ticker_data = await fetch_ticker_data_ultra_fast(coin_id)
    if not ticker_data or 'tickers' not in ticker_data or not ticker_data['tickers']:
        return 0, "No Exchange Data"
    
    tickers = ticker_data['tickers']
    total_volume = sum(float(t.get('converted_volume', {}).get('usd', 0) or 0) for t in tickers)
    if total_volume == 0:
        return 0, "No Volume Data"
    
    # Sort exchanges by volume
    exchange_volumes = {}
    for ticker in tickers:
        exchange = ticker.get('market', {}).get('name', 'Unknown')
        volume = float(ticker.get('converted_volume', {}).get('usd', 0) or 0)
        if exchange in exchange_volumes:
            exchange_volumes[exchange] += volume
        else:
            exchange_volumes[exchange] = volume
    
    sorted_exchanges = sorted(exchange_volumes.items(), key=lambda x: x[1], reverse=True)
    if not sorted_exchanges:
        return 0, "No Exchange Data"
    
    # Calculate concentration metrics
    top_exchange_share = sorted_exchanges[0][1] / total_volume
    exchange_count = len([ex for ex, vol in sorted_exchanges if vol > total_volume * 0.01])
    
    # Score distribution health
    distribution_score = 0
    distribution_status = "Healthy Distribution"
    
    if top_exchange_share > 0.9:
        distribution_score = -15
        distribution_status = "⚠️ Single Exchange Dominance"
    elif top_exchange_share > 0.7:
        distribution_score = -8
        distribution_status = "🔶 High Concentration Risk"
    elif top_exchange_share > 0.5:
        distribution_score = -3
        distribution_status = "🟡 Moderate Concentration"
    elif exchange_count >= 5:
        distribution_score = 10
        distribution_status = "🟢 Well Distributed"
    elif exchange_count >= 3:
        distribution_score = 5
        distribution_status = "✅ Good Distribution"
    else:
        distribution_score = 0
        distribution_status = "📊 Limited Distribution"
    
    # Check for manipulation-prone exchanges
    top_exchange = sorted_exchanges[0][0].lower()
    if any(sus in top_exchange for sus in ['unknown', 'dex', 'pancake', 'uniswap']) and top_exchange_share > 0.6:
        distribution_score -= 5
        distribution_status += " (DEX Heavy)"
    
    # Create distribution summary
    distribution_details = f"Top exchange controls {top_exchange_share:.1%} of trading"
    if len(sorted_exchanges) > 1 and exchange_count > 1:
        distribution_details += f" ({exchange_count} total exchanges)"
    
    return distribution_score, f"{distribution_status} - {distribution_details}"

async def calculate_fomo_status_ultra_fast_original(coin_data):
    """
    ORIGINAL FOMO calculation - COMPLETELY UNCHANGED
    Preserved for compatibility and comparison purposes
    """
    price_1h_change = coin_data.get('change_1h') or 0
    price_24h_change = coin_data.get('change_24h') or 0
    current_volume = coin_data.get('volume') or 0
    coin_id = coin_data.get('id', '')
    coin_symbol = coin_data.get('symbol', '').upper()
    
    logging.debug(f"Starting ORIGINAL FOMO calculation for {coin_id}")
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    # Run ALL analysis in parallel (preserving your existing structure)
    start_time = time.time()
    
    tasks = [
        calculate_volume_spike_ultra_fast_original(coin_id, current_volume),
        analyze_momentum_trend_ultra_fast_original(coin_id, current_volume, price_1h_change, price_24h_change),
        analyze_exchange_distribution_ultra_fast_original(coin_id)
    ]
    
    # Execute all API calls simultaneously
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Unpack results with error handling
    volume_spike = results[0] if not isinstance(results[0], Exception) else 1.0
    trend_result = results[1] if not isinstance(results[1], Exception) else (0, "Unknown")
    distribution_result = results[2] if not isinstance(results[2], Exception) else (0, "Analysis Failed")
    
    trend_score, trend_status = trend_result
    distribution_score, distribution_status = distribution_result
    
    elapsed = time.time() - start_time
    logging.info(f"✅ ORIGINAL analysis complete for {coin_id} in {elapsed:.2f}s: Volume={volume_spike:.1f}x, Trend={trend_status}")
    
    # =============================================================================
    # ORIGINAL FOMO CALCULATION (EXACTLY AS IT WAS)
    # =============================================================================
    
    fomo_score = 0
    signal_type = "No Signal"
    
    # Base score from volume spike (0-60 points) - UNCHANGED
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
    
    # Price movement modifiers - UNCHANGED
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
    
    # 1-hour momentum bonus/penalty - UNCHANGED
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    elif price_1h_change < 0 and price_24h_change > 0:
        fomo_score += 1
    
    # Volume size bonus/penalty - UNCHANGED
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
    
    # High price coin penalty - UNCHANGED
    coin_price = coin_data.get('price', 0) or 0
    try:
        coin_price = float(coin_price)
        if coin_price > 1000 and current_volume < 1_000_000:
            fomo_score -= 25
        elif coin_price > 100 and current_volume < 500_000:
            fomo_score -= 15
    except:
        pass
    
    # Add momentum trend score and exchange distribution score - UNCHANGED
    fomo_score += trend_score
    fomo_score += distribution_score
    
    # Ensure score stays within 0-100 range
    fomo_score = max(0, min(100, fomo_score))
    
    # Determine signal type - ORIGINAL LOGIC
    if fomo_score >= 85 and abs_24h_change < 5.0:
        signal_type = "🎯 Stealth Accumulation"
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
    
    # Override signal type with trend status if very strong - UNCHANGED
    if "🚀 Accelerating" in trend_status and fomo_score >= 60:
        signal_type = "🚀 Accelerating Breakout"
    elif "🔻 Losing Steam" in trend_status:
        signal_type = "🔻 Losing Steam"
    
    return fomo_score, signal_type, trend_status, distribution_status, volume_spike

# =============================================================================
# COMPATIBILITY FUNCTIONS
# =============================================================================

async def run_original_vs_enhanced_comparison(coin_data):
    """
    Compare original vs enhanced algorithms side by side
    Useful for testing and validation
    """
    print(f"\n🔍 COMPARING ALGORITHMS FOR {coin_data.get('symbol', 'UNKNOWN')}")
    print("=" * 60)
    
    try:
        # Run original algorithm
        original_result = await calculate_fomo_status_ultra_fast_original(coin_data)
        original_score, original_signal, original_trend, original_dist, original_vol = original_result
        
        print(f"📊 ORIGINAL ALGORITHM:")
        print(f"   Score: {original_score}%")
        print(f"   Signal: {original_signal}")
        print(f"   Volume Spike: {original_vol:.1f}x")
        
        # Run enhanced algorithm
        from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
        enhanced_result = await calculate_fomo_status_ultra_fast_v21(coin_data)
        enhanced_score, enhanced_signal, enhanced_trend, enhanced_dist, enhanced_vol = enhanced_result
        
        print(f"\n🚀 ENHANCED ALGORITHM:")
        print(f"   Score: {enhanced_score}%")
        print(f"   Signal: {enhanced_signal}")
        print(f"   Volume Spike: {enhanced_vol:.1f}x")
        
        # Show differences
        score_diff = enhanced_score - original_score
        print(f"\n✨ DIFFERENCES:")
        print(f"   Score Change: {score_diff:+.1f} points")
        print(f"   Signal Change: {original_signal} → {enhanced_signal}")
        
        # Analysis
        if score_diff < -10:
            print(f"   📉 Enhanced algorithm filtered this out (likely good)")
        elif score_diff > 10:
            print(f"   📈 Enhanced algorithm boosted this (likely opportunity)")
        else:
            print(f"   📊 Minimal change (both algorithms agree)")
        
        return {
            'original': original_result,
            'enhanced': enhanced_result,
            'score_difference': score_diff
        }
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return None

# =============================================================================
# BACKWARD COMPATIBILITY WRAPPERS
# =============================================================================

# Ensure all original function names are available
calculate_volume_spike_ultra_fast = calculate_volume_spike_ultra_fast_original
analyze_momentum_trend_ultra_fast = analyze_momentum_trend_ultra_fast_original  
analyze_exchange_distribution_ultra_fast = analyze_exchange_distribution_ultra_fast_original

print("✅ Part 3: Legacy Functions preserved!")
print("🎯 All original functions available:")
print("  - calculate_fomo_status() - sync version")
print("  - calculate_fomo_status_ultra_fast_original() - async original")
print("  - analyze_momentum_trend() - sync fallback")
print("  - analyze_exchange_distribution() - sync fallback")
print("  - calculate_real_volume_spike() - sync version")
print("🔄 100% backward compatibility maintained!")