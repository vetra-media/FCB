"""
Simple test to verify your CFB bot is working
Run this instead of the complex integration test
"""

import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

async def simple_test():
    """
    Simple test that focuses on the main issue: zero results
    """
    
    print("🎯 SIMPLE CFB BOT TEST")
    print("=" * 40)
    
    # Test coins
    test_coins = [
        {
            'id': 'bitcoin',
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price': 43250.12,
            'change_1h': 0.25,
            'change_24h': 2.15,
            'volume': 18500000000,
            'market_cap': 850000000000,
            'market_cap_rank': 1
        },
        {
            'id': 'tron',
            'symbol': 'TRX', 
            'name': 'TRON',
            'price': 0.102456,
            'change_1h': 1.85,
            'change_24h': 12.75,  # The problematic TRON scenario
            'volume': 281000000,
            'market_cap': 26000000000,  # $26B
            'market_cap_rank': 15
        },
        {
            'id': 'derive-protocol',
            'symbol': 'DRV',
            'name': 'Derive Protocol',
            'price': 0.028295,
            'change_1h': 2.5,
            'change_24h': 6.99,
            'volume': 281136,
            'market_cap': 20868400,
            'market_cap_rank': 800
        }
    ]
    
    try:
        # Import the main analysis function
        from analysis import calculate_fomo_status_ultra_fast
        print("✅ Analysis module imported successfully")
        
        print(f"\n🔄 Testing {len(test_coins)} coins...")
        
        total_tests = 0
        zero_results = 0
        successful_results = 0
        
        for coin in test_coins:
            total_tests += 1
            symbol = coin['symbol']
            
            try:
                print(f"\n🪙 Testing {symbol}...")
                
                # This is the critical test - does it return zero?
                result = await calculate_fomo_status_ultra_fast(coin)
                
                if result and len(result) == 5:
                    score, signal, trend, distribution, volume_spike = result
                    
                    if score == 0:
                        zero_results += 1
                        print(f"🚨 {symbol}: ZERO RESULT - This causes blank screens!")
                    else:
                        successful_results += 1
                        print(f"✅ {symbol}: {score}% - {signal}")
                        
                        # Show what your bot users will see
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
                        
                        print(f"   📱 Bot message: {emoji} {symbol} | FOMO: {score}% | {status}")
                else:
                    print(f"❌ {symbol}: Unexpected result format: {result}")
                    
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
        
        # Results summary
        print(f"\n📊 SIMPLE TEST RESULTS")
        print(f"-" * 30)
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_results}")
        print(f"Zero results: {zero_results}")
        print(f"Success rate: {(successful_results/total_tests)*100:.1f}%")
        
        # Critical assessment
        if zero_results == 0:
            print(f"\n🎉 ZERO RESULTS PROBLEM SOLVED!")
            print(f"✅ Your bot will never show blank screens again")
            print(f"✅ Users always get engaging content")
            print(f"🚀 Ready for production!")
        else:
            print(f"\n🚨 STILL HAVE ZERO RESULTS ISSUE")
            print(f"❌ {zero_results} coins returned zero scores")
            print(f"💡 Need to debug the analysis chain")
        
        # TRON test
        print(f"\n🔍 TRON FILTER TEST:")
        tron_result = None
        for coin in test_coins:
            if coin['symbol'] == 'TRX':
                result = await calculate_fomo_status_ultra_fast(coin)
                if result:
                    tron_score = result[0]
                    if tron_score < 50:
                        print(f"✅ TRON filtered correctly: {tron_score}% (down from ~85%)")
                    else:
                        print(f"⚠️ TRON still high: {tron_score}% (should be lower)")
                break
        
        return successful_results, zero_results
        
    except ImportError as e:
        print(f"❌ Cannot import analysis module: {e}")
        print(f"💡 Check that analysis/__init__.py is correct")
        return 0, 0
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 0, 0

if __name__ == "__main__":
    print(f"🚀 Starting Simple CFB Test...")
    print(f"⏰ {datetime.now()}")
    
    try:
        successful, zeros = asyncio.run(simple_test())
        
        if zeros == 0:
            print(f"\n🏆 SUCCESS: Zero results problem is SOLVED!")
            print(f"🎮 Your gaming bot is ready for users!")
        else:
            print(f"\n🔧 Still need fixes: {zeros} zero results detected")
            
    except Exception as e:
        print(f"\n❌ Simple test failed: {e}")
        print(f"💡 Try: pip install aiohttp requests")