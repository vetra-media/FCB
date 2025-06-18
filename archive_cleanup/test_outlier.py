import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_outlier_detection():
    print("🧪 TESTING OUTLIER DETECTION")
    print("=" * 40)
    
    from analysis import calculate_fomo_status_ultra_fast_enhanced
    
    # Test with a Derive-like outlier
    outlier_coin = {
        'id': 'test-outlier',
        'symbol': 'OUTLIER',
        'name': 'Test Outlier Token 2024',
        'price': 0.0234,
        'volume': 250000,           # Good volume for small cap
        'market_cap': 25000000,     # $25M - perfect outlier range
        'market_cap_rank': 850,     # Mid-tier ranking like Derive
        'change_1h': 1.5,
        'change_24h': -1.2          # Slight dip = accumulation opportunity
    }
    
    print(f"📊 Testing: {outlier_coin['symbol']}")
    print(f"   Market Cap: ${outlier_coin['market_cap']:,}")
    print(f"   Rank: #{outlier_coin['market_cap_rank']}")
    print(f"   Volume: ${outlier_coin['volume']:,}")
    
    try:
        result = await calculate_fomo_status_ultra_fast_enhanced(outlier_coin)
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = result
        
        print(f"\n🚀 ENHANCED RESULTS:")
        print(f"   FOMO Score: {fomo_score}")
        print(f"   Signal: {signal_type}")
        print(f"   Volume Spike: {volume_spike:.1f}x")
        
        if fomo_score >= 60:
            print(f"   🎯 RESULT: HIGH OPPORTUNITY DETECTED!")
        elif fomo_score >= 40:
            print(f"   🟡 RESULT: MODERATE OPPORTUNITY")
        else:
            print(f"   😐 RESULT: Low opportunity")
            
        print(f"\n✅ Outlier test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_outlier_detection())