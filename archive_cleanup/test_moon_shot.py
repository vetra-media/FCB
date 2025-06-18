import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_moon_shot():
    print("🌙 TESTING POTENTIAL MOON SHOT")
    print("=" * 40)
    
    from analysis import calculate_fomo_status_ultra_fast_enhanced
    
    # Perfect outlier conditions
    moon_shot = {
        'id': 'moon-shot-defi',
        'symbol': 'MOON',
        'name': 'MoonShot DeFi Protocol 2024',  # New token indicators
        'price': 0.00123,
        'volume': 750000,          # High volume for small cap
        'market_cap': 8000000,     # $8M - very small cap
        'market_cap_rank': 1800,   # Very low rank = big outlier bonus
        'change_1h': 2.1,          # Positive momentum 
        'change_24h': 4.5          # Good gain but not extreme
    }
    
    print(f"🚀 Testing: {moon_shot['symbol']}")
    print(f"   Market Cap: ${moon_shot['market_cap']:,} (micro-cap!)")
    print(f"   Rank: #{moon_shot['market_cap_rank']} (deep outlier!)")
    print(f"   Volume: ${moon_shot['volume']:,}")
    print(f"   24h Change: +{moon_shot['change_24h']}%")
    print(f"   Name has '2024': {('2024' in moon_shot['name'])}")
    
    try:
        result = await calculate_fomo_status_ultra_fast_enhanced(moon_shot)
        fomo_score, signal_type, trend_status, distribution_status, volume_spike = result
        
        print(f"\n🚀 ENHANCED RESULTS:")
        print(f"   FOMO Score: {fomo_score}")
        print(f"   Signal: {signal_type}")
        print(f"   Volume Spike: {volume_spike:.1f}x")
        
        if fomo_score >= 75:
            print(f"   🎯 RESULT: HIGH CONVICTION - Would be broadcast!")
        elif fomo_score >= 60:
            print(f"   🟡 RESULT: STRONG SIGNAL - Would be flagged!")
        elif fomo_score >= 40:
            print(f"   📈 RESULT: MODERATE - On the radar!")
        else:
            print(f"   😐 RESULT: Still building...")
            
        print(f"\n✅ Moon shot test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_moon_shot())