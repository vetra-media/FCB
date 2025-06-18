"""
FCB v2 System Integration Test
Comprehensive test of session_manager.py + token_economics.py + navigation_handler.py
"""

import logging
import time
import asyncio
from typing import Dict, Any

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all our systems
try:
    from session_manager import (
        get_user_session, add_to_user_history, navigate_back, navigate_forward,
        get_session_navigation_state, get_cached_coin_data, clear_user_session,
        debug_user_session, get_session_stats
    )
    print("✅ session_manager.py imported successfully")
except ImportError as e:
    print(f"❌ session_manager.py import failed: {e}")
    exit(1)

try:
    from token_economics import (
        get_user_balance, spend_fcb_token, add_fcb_tokens, 
        check_rate_limit_with_fcb, get_user_balance_info,
        record_purchase, get_system_statistics
    )
    print("✅ token_economics.py imported successfully")
except ImportError as e:
    print(f"❌ token_economics.py import failed: {e}")
    exit(1)

try:
    from navigation_handler import (
        NavigationResult, FCBNavigationHandler,
        handle_back, handle_next, get_navigation_buttons
    )
    print("✅ navigation_handler.py imported successfully")
except ImportError as e:
    print(f"❌ navigation_handler.py import failed: {e}")
    exit(1)

class FCBSystemTester:
    """Comprehensive test suite for FCB v2 systems"""
    
    def __init__(self):
        self.test_user_id = 99999  # Test user ID
        self.nav_handler = FCBNavigationHandler()
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if details:
            logger.info(f"    {details}")
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            
    def setup_test_environment(self):
        """Clean setup for testing"""
        logger.info("🧹 Setting up test environment...")
        
        # Clear any existing test user data
        clear_user_session(self.test_user_id)
        
        logger.info(f"📋 Using test user ID: {self.test_user_id}")
        
    def test_session_manager(self):
        """Test session management functionality"""
        logger.info("\n🔍 TESTING SESSION MANAGER")
        
        # Test 1: Create new session
        try:
            session = get_user_session(self.test_user_id)
            success = isinstance(session, dict) and 'history' in session
            self.log_test("Create new session", success, f"Session keys: {list(session.keys())}")
        except Exception as e:
            self.log_test("Create new session", False, f"Error: {e}")
        
        # Test 2: Add coin to history
        try:
            test_coin_data = {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'price': 50000,
                'market_cap': 1000000000
            }
            
            session = add_to_user_history(self.test_user_id, 'bitcoin', test_coin_data)
            success = len(session['history']) == 1 and session['history'][0] == 'bitcoin'
            self.log_test("Add coin to history", success, f"History: {session['history']}")
        except Exception as e:
            self.log_test("Add coin to history", False, f"Error: {e}")
        
        # Test 3: Check cached data
        try:
            cached_data = get_cached_coin_data(self.test_user_id, 'bitcoin')
            success = cached_data is not None and cached_data.get('symbol') == 'BTC'
            self.log_test("Get cached data", success, f"Cached symbol: {cached_data.get('symbol') if cached_data else 'None'}")
        except Exception as e:
            self.log_test("Get cached data", False, f"Error: {e}")
        
        # Test 4: Navigation state
        try:
            nav_state = get_session_navigation_state(self.test_user_id)
            success = nav_state is not None and nav_state['total_coins'] == 1
            self.log_test("Navigation state", success, f"Total coins: {nav_state.get('total_coins') if nav_state else 'None'}")
        except Exception as e:
            self.log_test("Navigation state", False, f"Error: {e}")
            
    def test_token_economics(self):
        """Test token economics functionality"""
        logger.info("\n💰 TESTING TOKEN ECONOMICS")
        
        # Test 1: Get user balance (new user)
        try:
            balance_info = get_user_balance(self.test_user_id)
            # New user should have: 0 FCB, 0 used, 0 bonus_used, 8 total_free (5 daily + 3 bonus)
            success = (balance_info[0] == 0 and  # fcb_balance
                      balance_info[1] == 0 and  # free_queries_used  
                      balance_info[2] == 0 and  # new_user_bonus_used
                      balance_info[3] == 8)     # total_free_remaining (5+3)
            self.log_test("New user balance", success, f"Balance: {balance_info}")
        except Exception as e:
            self.log_test("New user balance", False, f"Error: {e}")
        
        # Test 2: Balance info for UI
        try:
            balance_info = get_user_balance_info(self.test_user_id)
            success = (balance_info['fcb_balance'] == 0 and 
                      balance_info['total_scans'] == 8 and
                      balance_info['total_free_remaining'] == 8)
            self.log_test("Balance info format", success, f"UI info: {balance_info}")
        except Exception as e:
            self.log_test("Balance info format", False, f"Error: {e}")
        
        # Test 3: Rate limit check
        try:
            allowed, time_remaining, reason = check_rate_limit_with_fcb(self.test_user_id)
            success = allowed and reason == "Allowed"
            self.log_test("Rate limit check", success, f"Allowed: {allowed}, Reason: {reason}")
        except Exception as e:
            self.log_test("Rate limit check", False, f"Error: {e}")
        
        # Test 4: Spend free query
        try:
            spend_success, message = spend_fcb_token(self.test_user_id, "test_query")
            success = spend_success and "daily free" in message.lower()
            self.log_test("Spend free query", success, f"Message: {message}")
        except Exception as e:
            self.log_test("Spend free query", False, f"Error: {e}")
        
        # Test 5: Add FCB tokens
        try:
            add_success, new_balance = add_fcb_tokens(self.test_user_id, 10, "Test purchase")
            success = add_success and new_balance == 10
            self.log_test("Add FCB tokens", success, f"New balance: {new_balance}")
        except Exception as e:
            self.log_test("Add FCB tokens", False, f"Error: {e}")
            
    async def test_navigation_handler(self):
        """Test navigation handler integration"""
        logger.info("\n🧭 TESTING NAVIGATION HANDLER")
        
        # Mock update and context for testing
        class MockUpdate:
            pass
        
        class MockContext:
            pass
        
        update = MockUpdate()
        context = MockContext()
        
        # Test 1: Back navigation (should fail - no history to go back to)
        try:
            result = await self.nav_handler.handle_back_navigation(self.test_user_id, update, context)
            success = not result.success and "beginning" in result.error_message.lower()
            self.log_test("Back navigation (empty history)", success, f"Message: {result.error_message}")
        except Exception as e:
            self.log_test("Back navigation (empty history)", False, f"Error: {e}")
        
        # Add some test coins to history for navigation testing
        try:
            # Add first coin
            test_coin_1 = {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'price': 3000
            }
            add_to_user_history(self.test_user_id, 'ethereum', test_coin_1)
            
            # Add second coin
            test_coin_2 = {
                'symbol': 'ADA',
                'name': 'Cardano', 
                'price': 0.5
            }
            add_to_user_history(self.test_user_id, 'cardano', test_coin_2)
            
            logger.info("    Added test coins to history for navigation testing")
        except Exception as e:
            logger.error(f"    Failed to add test coins: {e}")
        
        # Test 2: Back navigation (should work now)
        try:
            result = await self.nav_handler.handle_back_navigation(self.test_user_id, update, context)
            success = result.success and result.cost_tokens == 0
            self.log_test("Back navigation (with history)", success, f"Success: {result.success}, Cost: {result.cost_tokens}")
        except Exception as e:
            self.log_test("Back navigation (with history)", False, f"Error: {e}")
        
        # Test 3: Forward navigation (should be FREE - using history)
        try:
            result = await self.nav_handler.handle_next_navigation(self.test_user_id, update, context)
            success = result.success and result.cost_tokens == 0
            self.log_test("Forward navigation (FREE history)", success, f"Success: {result.success}, Cost: {result.cost_tokens}")
        except Exception as e:
            self.log_test("Forward navigation (FREE history)", False, f"Error: {e}")
        
        # Test 4: Create navigation buttons
        try:
            buttons = self.nav_handler.create_navigation_buttons(self.test_user_id)
            success = buttons is not None and hasattr(buttons, 'inline_keyboard')
            button_count = len(buttons.inline_keyboard) if buttons and hasattr(buttons, 'inline_keyboard') else 0
            self.log_test("Create navigation buttons", success, f"Button rows: {button_count}")
        except Exception as e:
            self.log_test("Create navigation buttons", False, f"Error: {e}")
            
    def test_system_integration(self):
        """Test integration between all systems"""
        logger.info("\n🔗 TESTING SYSTEM INTEGRATION")
        
        # Test 1: Session + Token economics integration
        try:
            # Get session state
            nav_state = get_session_navigation_state(self.test_user_id)
            
            # Get balance info
            balance_info = get_user_balance_info(self.test_user_id)
            
            # Check integration
            success = (nav_state is not None and 
                      balance_info is not None and
                      'total_scans' in balance_info and
                      'can_go_back' in nav_state)
            
            self.log_test("Session + Token integration", success, 
                         f"Nav state keys: {list(nav_state.keys()) if nav_state else 'None'}, "
                         f"Balance keys: {list(balance_info.keys()) if balance_info else 'None'}")
        except Exception as e:
            self.log_test("Session + Token integration", False, f"Error: {e}")
        
        # Test 2: Rate limiting integration
        try:
            # Check rate limit
            allowed_1, _, _ = check_rate_limit_with_fcb(self.test_user_id)
            
            # Quick second check (should be rate limited)  
            allowed_2, time_remaining, reason = check_rate_limit_with_fcb(self.test_user_id)
            
            success = allowed_1 and not allowed_2 and reason == "Rate limited"
            self.log_test("Rate limiting integration", success, 
                         f"First: {allowed_1}, Second: {allowed_2}, Reason: {reason}")
        except Exception as e:
            self.log_test("Rate limiting integration", False, f"Error: {e}")
            
    def get_system_stats(self):
        """Get comprehensive system statistics"""
        logger.info("\n📊 SYSTEM STATISTICS")
        
        try:
            # Session stats
            session_stats = get_session_stats()
            logger.info(f"📱 Session Stats: {session_stats}")
            
            # Token economics stats  
            token_stats = get_system_statistics()
            logger.info(f"💰 Token Stats: {token_stats}")
            
            # User balance
            balance = get_user_balance_info(self.test_user_id)
            logger.info(f"👤 Test User Balance: {balance}")
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 STARTING FCB v2 SYSTEM TESTS")
        logger.info("=" * 50)
        
        # Setup
        self.setup_test_environment()
        
        # Run test suites
        self.test_session_manager()
        self.test_token_economics()
        await self.test_navigation_handler()
        self.test_system_integration()
        
        # Get stats
        self.get_system_stats()
        
        # Final results
        logger.info("\n" + "=" * 50)
        logger.info("🏁 TEST RESULTS SUMMARY")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        logger.info(f"📊 Success Rate: {(self.passed_tests / max(self.passed_tests + self.failed_tests, 1)) * 100:.1f}%")
        
        if self.failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! Your FCB v2 foundation is solid!")
            logger.info("🚀 Ready to build payment system or callback handlers!")
        else:
            logger.info("⚠️  Some tests failed. Check the logs above for details.")
            logger.info("🔧 Fix issues before proceeding to next development phase.")

# Test execution
async def main():
    """Main test execution"""
    tester = FCBSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🧪 FCB v2 System Integration Test")
    print("Testing session_manager.py + token_economics.py + navigation_handler.py")
    print("-" * 60)
    
    # Run the tests
    asyncio.run(main())
    
    print("\n🏁 Test completed! Check the logs above for detailed results.")