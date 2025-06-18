import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_real_scenario():
    print("🧪 TESTING REALISTIC PUMP SCENARIO")
    print("=" * 45)
    
    from analysis import calculate_fomo_status_ultra_fast_enhanced
    
    # Simulate a coin with volume spike and accumulation
    pump_coin = {
        'id': 'realistic-gem',
        'symbol': 'GEM',
        'name': 'Realistic Gem DeFi 2024',
        'price': 0.0856,
        'volume': 500000,           # Higher volume
        'market_cap': 15000000,     # $15M - small cap gem
        'market_cap_rank': 1200,    # Lower rank = more outlier bonus
        'change_1h': 3.2,           # Some upward momentum
        'change_24h': 1.8           # Small gain (not already pumped)
    }
    
    print(f"📊 Testing: {pump_coin['symbol']}")
    print(f"   Market Cap: ${pump_coin['market_cap']:,}")
    print(f"   Rank: #{pump_coin['market_cap_rank']}")
    print(f"   Volume: ${pump_coin['volume']:,}")
    print(f"   24h Change: +{pump_coin['change_24h']}%")
    
    # Test both original and enhanced
    print(f"\n🔄 COMPARISON TEST:")
    
    try:
        # Original algorithm (v2.1)
        from analysis import calculate_fomo_status_ultra_fast_v21
        original_result = await calculate_fomo_status_ultra_fast_v21(pump_coin)
        original_score = original_result[0]
        original_signal = original_result[1]
        
        # Enhanced algorithm
        enhanced_result = await calculate_fomo_status_ultra_fast_enhanced(pump_coin)
        enhanced_score = enhanced_result[0]
        enhanced_signal = enhanced_result[1]
        
        print(f"📈 ORIGINAL v2.1:")
        print(f"   Score: {original_score}")
        print(f"   Signal: {original_signal}")
        
        print(f"\n🚀 ENHANCED v2.2:")
        print(f"   Score: {enhanced_score}")
        print(f"   Signal: {enhanced_signal}")
        
        improvement = enhanced_score - original_score
        print(f"\n✨ IMPROVEMENT: +{improvement} points")
        
        if enhanced_score >= 70:
            print(f"   🎯 RESULT: HIGH OPPORTUNITY!")
        elif enhanced_score >= 50:
            print(f"   🟡 RESULT: MODERATE OPPORTUNITY")
        elif improvement > 0:
            print(f"   📈 RESULT: Enhanced scoring working!")
        else:
            print(f"   😐 RESULT: Low opportunity")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_scenario())