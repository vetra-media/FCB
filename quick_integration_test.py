"""
quick_integration_test.py - Test your CFB bot integration

This script tests the integration between your analysis system and handlers
Run this to verify everything works before deploying

USAGE:
    python quick_integration_test.py
"""

import asyncio
import logging
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample coin data that mimics your real data flow
SAMPLE_COINS = [
    {
        'id': 'bitcoin',
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'current_price': 43250.12,
        'price_change_percentage_1h_in_currency': 0.25,
        'price_change_percentage_24h_in_currency': 2.15,
        'total_volume': 18500000000,
        'market_cap': 850000000000,
        'market_cap_rank': 1
    },
    {
        'id': 'ethereum',
        'symbol': 'ETH', 
        'name': 'Ethereum',
        'current_price': 2750.85,
        'price_change_percentage_1h_in_currency': 1.2,
        'price_change_percentage_24h_in_currency': 4.8,
        'total_volume': 12000000000,
        'market_cap': 330000000000,
        'market_cap_rank': 2
    },
    {
        'id': 'derive-protocol',
        'symbol': 'DRV',
        'name': 'Derive Protocol',
        'current_price': 0.028295,
        'price_change_percentage_1h_in_currency': 2.5,
        'price_change_percentage_24h_in_currency': 6.99,
        'total_volume': 281136,
        'market_cap': 20868400,
        'market_cap_rank': 800
    }
]

def normalize_coin_data(coin_data):
    """Convert to your analysis format"""
    return {
        'id': coin_data.get('id', ''),
        'symbol': coin_data.get('symbol', ''),
        'name': coin_data.get('name', ''),
        'price': coin_data.get('current_price', 0),
        'change_1h': coin_data.get('price_change_percentage_1h_in_currency', 0),
        'change_24h': coin_data.get('price_change_percentage_24h_in_currency', 0),
        'volume': coin_data.get('total_volume', 0),
        'market_cap': coin_data.get('market_cap', 0),
        'market_cap_rank': coin_data.get('market_cap_rank', 999999)
    }

async def test_analysis_import():
    """Test that analysis module imports correctly"""
    print("🔄 Testing analysis module import...")
    
    try:
        # This is what your scanner.py does
        from analysis import calculate_fomo_status_ultra_fast
        
        print("✅ Analysis module imported successfully")
        return True, calculate_fomo_status_ultra_fast
        
    except Exception as e:
        print(f"❌ Analysis import failed: {e}")
        return False, None

async def test_single_coin_analysis(analysis_func, coin_data):
    """Test analysis on a single coin"""
    normalized_coin = normalize_coin_data(coin_data)
    symbol = normalized_coin['symbol']
    
    print(f"🔄 Testing {symbol} analysis...")
    
    try:
        # This mimics what your handlers do
        result = await analysis_func(normalized_coin)
        
        if result and len(result) == 5:
            score, signal, trend, distribution, volume_spike = result
            
            # Check for zero results (your main problem)
            if score == 0:
                print(f"🚨 ZERO RESULT for {symbol} - This is the problem!")
                return False, f"Zero score: {score}"
            
            print(f"✅ {symbol}: {score}% - {signal}")
            print(f"   📊 Trend: {trend[:40]}...")
            print(f"   💧 Volume: {volume_spike:.1f}x")
            
            return True, f"Score: {score}%"
            
        else:
            print(f"❌ {symbol}: Unexpected result format: {result}")
            return False, f"Bad format: {result}"
            
    except Exception as e:
        print(f"❌ {symbol} analysis failed: {e}")
        return False, str(e)

async def test_message_formatting(analysis_results):
    """Test how results would appear in bot messages"""
    print("\n💬 Testing message formatting...")
    
    try:
        # This mimics your formatters.py
        for coin_data, (success, result_data) in analysis_results.items():
            symbol = coin_data['symbol']
            
            if success and "Score:" in result_data:
                # Extract score for formatting test
                score_str = result_data.split("Score: ")[1].split("%")[0]
                score = float(score_str)
                
                # Test your bot message format
                if score >= 70:
                    emoji = "🚀"
                    status = "HIGH CONVICTION"
                elif score >= 60:
                    emoji = "⚡"
                    status = "GOOD OPPORTUNITY"
                elif score >= 50:
                    emoji = "📈"
                    status = "MODERATE"
                else:
                    emoji = "👀"
                    status = "WATCH"
                
                message = f"{emoji} {symbol}\nFOMO: {score}%\n{status}"
                print(f"✅ {symbol} message: {message.replace(chr(10), ' | ')}")
            else:
                print(f"❌ {symbol} message: Cannot format - {result_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message formatting failed: {e}")
        return False

async def test_batch_processing(analysis_func):
    """Test batch processing like your scanner does"""
    print("\n📦 Testing batch processing...")
    
    try:
        # This mimics your scanner.py batch processing
        tasks = []
        for coin_data in SAMPLE_COINS:
            normalized_coin = normalize_coin_data(coin_data)
            tasks.append(analysis_func(normalized_coin))
        
        # Run all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = 0
        zero_results = 0
        
        for i, result in enumerate(results):
            symbol = SAMPLE_COINS[i]['symbol']
            
            if isinstance(result, Exception):
                print(f"❌ {symbol}: Exception - {result}")
            elif result and len(result) == 5:
                score = result[0]
                if score == 0:
                    zero_results += 1
                    print(f"🚨 {symbol}: ZERO RESULT")
                else:
                    successful_results += 1
                    print(f"✅ {symbol}: {score}%")
            else:
                print(f"❌ {symbol}: Bad format - {result}")
        
        print(f"\n📊 Batch results: {successful_results} success, {zero_results} zero results")
        
        if zero_results > 0:
            print(f"🚨 CRITICAL: {zero_results} coins returned zero results")
            print("   This is why your bot shows blank screens!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False

async def test_error_scenarios():
    """Test how system handles bad data"""
    print("\n🚨 Testing error scenarios...")
    
    bad_data_tests = [
        {'symbol': 'TEST', 'price': None, 'volume': 0},  # No volume
        {'symbol': 'BAD'},  # Missing fields
        {},  # Empty data
        {'symbol': 'ERR', 'price': 'invalid', 'volume': 'bad'}  # Invalid types
    ]
    
    try:
        from analysis import calculate_fomo_status_ultra_fast
        
        for i, bad_data in enumerate(bad_data_tests):
            print(f"🔄 Testing bad data #{i+1}...")
            
            try:
                result = await calculate_fomo_status_ultra_fast(bad_data)
                
                if result and len(result) == 5 and result[0] > 0:
                    print(f"✅ Bad data #{i+1}: Handled gracefully - {result[0]}%")
                else:
                    print(f"⚠️ Bad data #{i+1}: Returned zero/invalid - {result}")
                    
            except Exception as e:
                print(f"❌ Bad data #{i+1}: Exception - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scenario test failed: {e}")
        return False

async def run_full_integration_test():
    """Run complete integration test"""
    print("🎯 CFB BOT INTEGRATION TEST")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Import
    success, analysis_func = await test_analysis_import()
    test_results['import'] = success
    
    if not success:
        print("\n❌ CRITICAL: Cannot import analysis module")
        print("   Fix this before running any other tests")
        return test_results
    
    # Test 2: Individual coin analysis
    print("\n🪙 Testing individual coin analysis...")
    analysis_results = {}
    
    for coin_data in SAMPLE_COINS:
        success, result_data = await test_single_coin_analysis(analysis_func, coin_data)
        analysis_results[coin_data] = (success, result_data)
        test_results[f"coin_{coin_data['symbol']}"] = success
    
    # Test 3: Message formatting
    success = await test_message_formatting(analysis_results)
    test_results['formatting'] = success
    
    # Test 4: Batch processing
    success = await test_batch_processing(analysis_func)
    test_results['batch'] = success
    
    # Test 5: Error handling
    success = await test_error_scenarios()
    test_results['error_handling'] = success
    
    # Generate report
    print("\n📋 INTEGRATION TEST REPORT")
    print("-" * 40)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your CFB bot integration is working correctly")
        print("🚀 Ready for production deployment")
    elif passed >= total * 0.8:
        print("⚠️ MOSTLY WORKING")
        print("🔧 Fix the failing tests for optimal performance")
    else:
        print("🚨 MAJOR ISSUES DETECTED")
        print("💡 Review the diagnostic output and apply fixes")
        print("📋 Most likely issues:")
        print("   - Zero results from analysis functions")
        print("   - Import/dependency problems")
        print("   - Missing error handling")
    
    # Specific recommendations
    zero_result_issues = [name for name, result in test_results.items() if not result and 'coin_' in name]
    if zero_result_issues:
        print(f"\n🚨 ZERO RESULT ISSUES: {len(zero_result_issues)} coins")
        print("   SOLUTION: Replace analysis/__init__.py with bulletproof version")
        print("   This will eliminate blank results permanently")
    
    return test_results

if __name__ == "__main__":
    try:
        print("🚀 Starting CFB Bot Integration Test...")
        print(f"⏰ Timestamp: {datetime.now()}")
        
        # Run the test
        results = asyncio.run(run_full_integration_test())
        
        print(f"\n✅ Integration test complete!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed to run: {e}")
        print(f"📋 Error: {traceback.format_exc()}")
        print("\n💡 This usually means:")
        print("   - analysis module not found")
        print("   - Missing dependencies") 
        print("   - Python path issues")
        print("   - Import circular dependency")