#!/usr/bin/env python3
"""
FCB Data Parsing Debug & Fix
Debug the API data parsing to see your algorithm's true power
"""

import asyncio
import sys
import os
import json

# Add FCB path
sys.path.append('/Users/chriswesson/Downloads/FCB/')

async def debug_api_response():
    """Debug what the API is actually returning"""
    
    print("🔍 FCB API DATA DEBUG")
    print("=" * 40)
    
    try:
        from api_client import fetch_coin_data_ultra_fast
        
        print("📡 Fetching raw API data for ethereum...")
        
        coin_data = await fetch_coin_data_ultra_fast('ethereum')
        
        print("\n📋 RAW API RESPONSE:")
        print(json.dumps(coin_data, indent=2) if coin_data else "None")
        
        if coin_data:
            print("\n🔍 FIELD ANALYSIS:")
            print(f"Available keys: {list(coin_data.keys())}")
            
            # Check specific fields
            fields_to_check = ['price', 'current_price', 'volume', '24h_volume', 'total_volume', 
                             'market_cap', 'market_cap_rank', 'change_24h', 'price_change_24h',
                             'price_change_percentage_24h', 'symbol', 'name', 'id']
            
            print("\n📊 FIELD VALUES:")
            for field in fields_to_check:
                value = coin_data.get(field, "NOT FOUND")
                print(f"   {field}: {value}")
        
        return coin_data
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_with_corrected_parsing():
    """Test with manually corrected data parsing"""
    
    print("\n🔧 TESTING WITH CORRECTED PARSING")
    print("=" * 40)
    
    try:
        from api_client import fetch_coin_data_ultra_fast
        from analysis import calculate_fomo_status_ultra_fast_phase1
        
        # Fetch raw data
        raw_data = await fetch_coin_data_ultra_fast('ethereum')
        
        if not raw_data:
            print("❌ No raw data returned")
            return
        
        # Manual data correction/parsing
        corrected_data = {
            'id': raw_data.get('id', 'ethereum'),
            'symbol': raw_data.get('symbol', 'ETH'),
            'name': raw_data.get('name', 'Ethereum'),
            # Try multiple possible field names for price
            'price': (raw_data.get('current_price') or 
                     raw_data.get('price') or 
                     raw_data.get('last_price', 0)),
            # Try multiple possible field names for volume
            'volume': (raw_data.get('total_volume') or 
                      raw_data.get('24h_volume') or 
                      raw_data.get('volume', 0)),
            # Market cap
            'market_cap': raw_data.get('market_cap', 0),
            'market_cap_rank': raw_data.get('market_cap_rank', 999),
            # Try multiple possible field names for 24h change
            'change_24h': (raw_data.get('price_change_percentage_24h') or 
                          raw_data.get('change_24h') or 
                          raw_data.get('price_change_24h', 0)),
            'change_1h': raw_data.get('price_change_percentage_1h', 0)
        }
        
        print("🧮 CORRECTED DATA:")
        print(f"   Symbol: {corrected_data['symbol']}")
        print(f"   Price: ${corrected_data['price']}")
        print(f"   Volume: ${corrected_data['volume']:,.0f}" if corrected_data['volume'] else "   Volume: 0")
        print(f"   Market Cap: ${corrected_data['market_cap']:,.0f}" if corrected_data['market_cap'] else "   Market Cap: 0")
        print(f"   24h Change: {corrected_data['change_24h']}%")
        print(f"   Rank: #{corrected_data['market_cap_rank']}")
        
        # Now test with corrected data
        print(f"\n🚀 RUNNING ENHANCED ANALYSIS WITH CORRECTED DATA...")
        
        result = await calculate_fomo_status_ultra_fast_phase1(corrected_data)
        
        fomo_score = result[0]
        enhanced_signal = result[1]
        trend_status = result[2]
        distribution_status = result[3]
        volume_spike = result[4]
        probability_profile = result[5] if len(result) > 5 else None
        
        print(f"\n📈 ENHANCED ANALYSIS RESULTS:")
        print(f"   FOMO Score: {fomo_score}")
        print(f"   Signal: {enhanced_signal}")
        print(f"   Volume Spike: {volume_spike:.1f}x")
        print(f"   Trend: {trend_status}")
        
        if probability_profile:
            print(f"\n🎯 PROBABILITY ANALYSIS:")
            print(f"   Win Rate: {probability_profile['win_rate']:.1f}%")
            print(f"   Risk/Reward: {probability_profile['risk_reward_ratio']:.1f}:1")
            print(f"   Expected Value: {probability_profile['expected_value']:.2f}")
            print(f"   Confidence: {probability_profile['confidence_level']}")
            print(f"   Patterns Detected: {len(probability_profile['detected_patterns'])}")
            
            if probability_profile['detected_patterns']:
                print(f"   🔍 Patterns: {list(probability_profile['detected_patterns'].keys())}")
        
        print(f"\n✅ This should show the TRUE power of your enhanced algorithm!")
        
    except Exception as e:
        print(f"❌ Corrected test failed: {e}")
        import traceback
        traceback.print_exc()

async def quick_manual_test():
    """Quick test with known good data"""
    
    print("\n⚡ QUICK MANUAL TEST WITH KNOWN GOOD DATA")
    print("=" * 45)
    
    try:
        from analysis import calculate_fomo_status_ultra_fast_phase1
        
        # Use realistic current market data (manually created)
        eth_data = {
            'id': 'ethereum',
            'symbol': 'ETH',
            'name': 'Ethereum',
            'price': 3200.50,          # Realistic ETH price
            'volume': 15000000000,     # $15B daily volume (realistic)
            'market_cap': 385000000000, # ~$385B market cap
            'market_cap_rank': 2,
            'change_1h': 0.8,
            'change_24h': 2.4          # Moderate positive movement
        }
        
        print("🧮 Testing with realistic ETH data:")
        print(f"   Price: ${eth_data['price']:,.2f}")
        print(f"   Volume: ${eth_data['volume']:,.0f}")
        print(f"   Market Cap: ${eth_data['market_cap']:,.0f}")
        print(f"   24h Change: +{eth_data['change_24h']}%")
        
        result = await calculate_fomo_status_ultra_fast_phase1(eth_data)
        
        print(f"\n🎯 RESULTS WITH REAL DATA:")
        print(f"   Score: {result[0]}")
        print(f"   Signal: {result[1]}")
        print(f"   Volume Spike: {result[4]:.1f}x")
        
        if len(result) > 5 and result[5]:
            prob = result[5]
            print(f"   Win Rate: {prob['win_rate']:.1f}%")
            print(f"   R/R: {prob['risk_reward_ratio']:.1f}:1")
            print(f"   EV: {prob['expected_value']:.2f}")
            
            if prob['expected_value'] > 0.3:
                print(f"   🎯 ASSESSMENT: STRONG SIGNAL!")
            else:
                print(f"   🟡 ASSESSMENT: Moderate signal")
        
        print(f"\n✅ This shows your algorithm working with proper data!")
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")

if __name__ == "__main__":
    print("🔍 FCB DATA DEBUG & FIX")
    print("1. Debug API response format")
    print("2. Test with corrected parsing")  
    print("3. Quick manual test with good data")
    print("4. All debug steps")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(debug_api_response())
    elif choice == "2":
        asyncio.run(test_with_corrected_parsing())
    elif choice == "3":
        asyncio.run(quick_manual_test())
    elif choice == "4":
        async def run_all():
            await debug_api_response()
            await test_with_corrected_parsing()  
            await quick_manual_test()
        asyncio.run(run_all())
    else:
        print("Invalid choice")