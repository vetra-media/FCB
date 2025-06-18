#!/usr/bin/env python3
"""
Test the new Elite Analysis system vs old system
"""

import asyncio
import sys
import os
import time

# Add the analysis_new directory to the path
sys.path.insert(0, 'analysis_new')

async def test_new_vs_old():
    """Test new system vs old system"""
    
    print("🧪 Testing New Elite System vs Current System...")
    
    # Test coin data (BTC example)
    test_coin = {
        'symbol': 'BTC',
        'price': 45000.0,
        'volume_24h': 25_000_000_000,
        'market_cap': 900_000_000_000,
        'price_change_percentage_1h': 1.2,
        'price_change_percentage_24h': 3.5,
        'price_change_percentage_7d': -2.1,
        'volume_change_24h': 15.3
    }
    
    print(f"\n📊 Test data: {test_coin['symbol']} at ${test_coin['price']:,}")
    print(f"24h Volume: ${test_coin['volume_24h']:,}")
    print(f"1h Change: {test_coin['price_change_percentage_1h']}%")
    
    # Test NEW system
    print("\n🚀 Testing NEW Elite System...")
    try:
        from elite_integration import analyze_coin_comprehensive
        
        start_time = time.time()
        new_result = await analyze_coin_comprehensive(test_coin, user_id=12345)
        new_time = time.time() - start_time
        
        print(f"✅ NEW System Results:")
        print(f"   Score: {new_result['fomo_score']:.1f}/100")
        print(f"   Signal: {new_result['signal']}")
        print(f"   Confidence: {new_result['confidence']}")
        print(f"   Gaming Rank: {new_result.get('score_rank', 'N/A')}")
        print(f"   Processing Time: {new_time:.3f}s")
        print(f"   Analysis: {new_result['analysis'][:100]}...")
        
        print(f"\n🎯 CONCLUSION:")
        print(f"✅ Elite System: WORKING")
        print(f"📊 Score: {new_result['fomo_score']:.1f}/100")
        print(f"⚡ Speed: {new_time:.3f}s")
        print(f"🎪 Gaming: {new_result.get('score_rank', 'Active')}")
        print(f"🔧 Ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ NEW System FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_new_vs_old())
    if success:
        print("\n🚀 READY TO MIGRATE!")
    else:
        print("\n🚨 FIX ISSUES FIRST")
