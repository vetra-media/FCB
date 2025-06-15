import asyncio
import sys
import os

# Add your project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_integration():
    print("🧪 TESTING INTEGRATION")
    print("=" * 40)
    
    try:
        # Test imports
        from analysis import calculate_fomo_status_ultra_fast, calculate_fomo_status_ultra_fast_enhanced
        from scanner import calculate_fomo_status_cg_predictive
        print("✅ All imports successful")
        
        # Test coin data
        test_coin = {
            'id': 'bitcoin',
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price': 50000,
            'volume': 1000000,
            'market_cap': 800000000000,
            'market_cap_rank': 1,
            'change_1h': 1.2,
            'change_24h': 3.5
        }
        
        # Test main function
        result = await calculate_fomo_status_ultra_fast(test_coin)
        print(f"✅ Main function works: Score={result[0]}")
        
        # Test enhanced function
        enhanced_result = await calculate_fomo_status_ultra_fast_enhanced(test_coin)
        print(f"✅ Enhanced function works: Score={enhanced_result[0]}")
        
        # Test scanner function
        scanner_coin = {
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'current_price': 50000,
            'total_volume': 1000000,
            'market_cap': 800000000000,
            'market_cap_rank': 1,
            'price_change_percentage_1h_in_currency': 1.2,
            'price_change_percentage_24h_in_currency': 3.5,
            'image': 'https://example.com/btc.png'
        }
        
        scanner_result = await calculate_fomo_status_cg_predictive(scanner_coin)
        print(f"✅ Scanner function works: Score={scanner_result['fomo_score']}")
        
        print("\n🎯 Integration test PASSED!")
        print(f"📊 Results:")
        print(f"   Main Score: {result[0]}")
        print(f"   Enhanced Score: {enhanced_result[0]}")
        print(f"   Scanner Score: {scanner_result['fomo_score']}")
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integration())