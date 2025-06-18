#!/usr/bin/env python3
"""
FCB v2 Integration Test
Run this to test all systems are working properly
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_fcb_v2_integration():
    """Complete integration test for FCB v2"""
    
    print("🧪 FCB v2 Integration Test Starting...")
    print("=" * 50)
    
    test_user_id = 999999  # Test user ID
    test_results = []
    
    # Test 1: Token Economics
    print("\n📊 Test 1: Token Economics")
    try:
        from token_economics import get_user_balance_info, debug_user_balance
        
        balance_info = get_user_balance_info(test_user_id)
        print(f"✅ Balance info: {balance_info}")
        
        if balance_info['total_scans'] > 0:
            test_results.append("✅ Token Economics: PASS")
        else:
            test_results.append("❌ Token Economics: FAIL - No scans available")
            
    except Exception as e:
        print(f"❌ Token Economics test failed: {e}")
        test_results.append("❌ Token Economics: ERROR")
    
    # Test 2: Session Management
    print("\n📱 Test 2: Session Management")
    try:
        from session_manager import get_user_session, add_to_user_history
        
        session = get_user_session(test_user_id)
        print(f"✅ Session created: {session}")
        
        # Add test coin to history
        test_coin_data = {
            'symbol': 'TEST',
            'name': 'Test Coin',
            'price': 0.001,
            'fomo_score': 75.5
        }
        
        session = add_to_user_history(test_user_id, 'test-coin', test_coin_data)
        print(f"✅ Added coin to history")
        
        test_results.append("✅ Session Management: PASS")
        
    except Exception as e:
        print(f"❌ Session Management test failed: {e}")
        test_results.append("❌ Session Management: ERROR")
    
    # Test 3: Elite Discovery
    print("\n🔍 Test 3: Elite Discovery")
    try:
        from elite_discovery_integration import discover_new_coin_with_elite, get_elite_discovery_status
        
        status = get_elite_discovery_status()
        print(f"✅ Discovery status: {status}")
        
        # Try discovery
        discovery_result = await discover_new_coin_with_elite(test_user_id)
        
        if discovery_result:
            print(f"✅ Discovery result: {discovery_result['symbol']} (FOMO: {discovery_result.get('fomo_score', 0):.1f})")
            test_results.append("✅ Elite Discovery: PASS")
        else:
            print("⚠️ Discovery returned None")
            test_results.append("⚠️ Elite Discovery: PARTIAL")
            
    except Exception as e:
        print(f"❌ Elite Discovery test failed: {e}")
        test_results.append("❌ Elite Discovery: ERROR")
    
    # Test 4: Navigation Handler
    print("\n🧭 Test 4: Navigation Handler")
    try:
        from navigation_handler import get_navigation_buttons, get_session_navigation_state
        
        nav_state = get_session_navigation_state(test_user_id)
        print(f"✅ Navigation state: {nav_state}")
        
        buttons = get_navigation_buttons(test_user_id)
        print(f"✅ Navigation buttons created")
        
        test_results.append("✅ Navigation Handler: PASS")
        
    except Exception as e:
        print(f"❌ Navigation Handler test failed: {e}")
        test_results.append("❌ Navigation Handler: ERROR")
    
    # Test 5: Command Handlers
    print("\n🎮 Test 5: Command Handlers")
    try:
        from command_handlers import command_handler
        
        # Mock update and context for testing
        class MockUser:
            def __init__(self):
                self.id = test_user_id
                self.username = "testuser"
                self.first_name = "Test"
        
        class MockUpdate:
            def __init__(self):
                self.effective_user = MockUser()
        
        mock_update = MockUpdate()
        mock_context = None
        
        # Test start command
        result = await command_handler.handle_start_command(mock_update, mock_context)
        
        if result.success:
            print("✅ Start command works")
            test_results.append("✅ Command Handlers: PASS")
        else:
            print("❌ Start command failed")
            test_results.append("❌ Command Handlers: FAIL")
            
    except Exception as e:
        print(f"❌ Command Handlers test failed: {e}")
        test_results.append("❌ Command Handlers: ERROR")
    
    # Test 6: Elite Analysis
    print("\n🏆 Test 6: Elite Analysis")
    try:
        from elite_engine import get_gaming_fomo_score, is_elite_engine_available
        
        available = is_elite_engine_available()
        print(f"✅ Elite engine available: {available}")
        
        # Test analysis
        test_coin = {
            'symbol': 'TEST',
            'price': 0.001,
            'volume': 1_000_000,
            'change_1h': 5.0,
            'change_24h': 10.0
        }
        
        analysis = await get_gaming_fomo_score(test_coin)
        print(f"✅ Analysis result: {analysis}")
        
        if analysis and 'score' in analysis:
            test_results.append("✅ Elite Analysis: PASS")
        else:
            test_results.append("❌ Elite Analysis: FAIL")
            
    except Exception as e:
        print(f"❌ Elite Analysis test failed: {e}")
        test_results.append("❌ Elite Analysis: ERROR")
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY:")
    print("=" * 50)
    
    for result in test_results:
        print(result)
    
    passed = len([r for r in test_results if "✅" in r and "PASS" in r])
    total = len(test_results)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! FCB v2 is ready to go!")
    elif passed >= total * 0.8:
        print("⚡ MOSTLY WORKING! Minor issues to fix.")
    else:
        print("🚨 MAJOR ISSUES! Need debugging.")
    
    # Specific debugging hints
    print("\n🔧 DEBUGGING HINTS:")
    if "❌ Token Economics" in str(test_results):
        print("• Check database initialization")
        print("• Verify NEW_USER_BONUS and FREE_QUERIES_PER_DAY constants")
    
    if "❌ Elite Discovery" in str(test_results):
        print("• Check elite_discovery_integration.py imports")
        print("• Verify elite_engine.py is working")
    
    if "❌ Navigation Handler" in str(test_results):
        print("• Check navigation_handler.py class indentation")
        print("• Verify _discover_new_coin method is part of class")

# Quick fix script
async def quick_fix_fcb():
    """Quick fix for common issues"""
    print("🔧 Running quick fixes...")
    
    # Fix 1: Ensure database is initialized
    try:
        from token_economics import db_manager
        db_manager.init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
    
    # Fix 2: Test user gets scans
    try:
        from token_economics import ensure_user_has_scans
        ensure_user_has_scans(999999)
        print("✅ Test user has scans")
    except Exception as e:
        print(f"❌ Could not ensure scans: {e}")
    
    print("🔧 Quick fixes complete!")

if __name__ == "__main__":
    # Run the integration test
    asyncio.run(test_fcb_v2_integration())
    
    print("\n" + "="*50)
    print("🔧 Would you like to run quick fixes? (y/n)")
    
    # For automated testing, always run quick fixes
    print("🔧 Running quick fixes automatically...")
    asyncio.run(quick_fix_fcb())