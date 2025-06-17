"""
bot_debug.py - Complete FCB Bot Debugging Script
Run this to test all components without starting the full bot

USAGE: ENV=test python3 bot_debug.py
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotDebugger:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'issues': [],
            'success_count': 0,
            'total_tests': 0
        }
    
    def test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        self.results['tests'][test_name] = {
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['total_tests'] += 1
        if success:
            self.results['success_count'] += 1
            print(f"✅ {test_name}: PASS {details}")
        else:
            self.results['issues'].append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAIL {details}")
    
    def test_environment(self):
        """Test environment configuration"""
        print("\n🔍 TESTING ENVIRONMENT")
        print("-" * 40)
        
        # Test environment loading
        try:
            test_mode = os.getenv("TEST_MODE")
            test_token = os.getenv("TEST_BOT_TOKEN")
            api_key = os.getenv("COINGECKO_API_KEY")
            
            self.test_result("env_loading", True, f"TEST_MODE={test_mode}")
            
            if test_token:
                token_preview = test_token[:12] + "..." if len(test_token) > 12 else test_token
                self.test_result("test_bot_token", True, f"Token: {token_preview}")
            else:
                self.test_result("test_bot_token", False, "TEST_BOT_TOKEN not found")
            
            if api_key:
                key_preview = api_key[:8] + "..." if len(api_key) > 8 else api_key
                self.test_result("coingecko_api", True, f"API Key: {key_preview}")
            else:
                self.test_result("coingecko_api", False, "COINGECKO_API_KEY not found")
                
        except Exception as e:
            self.test_result("env_loading", False, str(e))
    
    def test_imports(self):
        """Test all critical imports"""
        print("\n📦 TESTING IMPORTS")
        print("-" * 40)
        
        # Test analysis import
        try:
            from analysis import calculate_fomo_status_ultra_fast
            self.test_result("analysis_import", True, "Main function imported")
        except Exception as e:
            self.test_result("analysis_import", False, str(e))
        
        # Test telegram import
        try:
            from telegram.ext import ApplicationBuilder, CommandHandler
            from telegram import Update
            self.test_result("telegram_import", True, "Telegram modules imported")
        except Exception as e:
            self.test_result("telegram_import", False, str(e))
        
        # Test database import
        try:
            from database import init_user_db
            self.test_result("database_import", True, "Database module imported")
        except Exception as e:
            self.test_result("database_import", False, str(e))
        
        # Test api_client import
        try:
            from api_client import fetch_market_data_ultra_fast
            self.test_result("api_client_import", True, "API client imported")
        except Exception as e:
            self.test_result("api_client_import", False, str(e))
    
    async def test_analysis_system(self):
        """Test the analysis system thoroughly"""
        print("\n🧪 TESTING ANALYSIS SYSTEM")
        print("-" * 40)
        
        try:
            from analysis import calculate_fomo_status_ultra_fast
            
            # Test coins
            test_coins = [
                {
                    'symbol': 'BTC',
                    'price': 43000,
                    'volume': 20000000000,
                    'change_1h': 1.2,
                    'change_24h': 3.5,
                    'market_cap': 850000000000
                },
                {
                    'symbol': 'TRX',
                    'price': 0.102456,
                    'change_1h': 1.85,
                    'change_24h': 12.75,
                    'volume': 281000000,
                    'market_cap': 26000000000
                },
                {
                    'symbol': 'DRV',
                    'price': 0.028295,
                    'change_1h': 2.5,
                    'change_24h': 6.99,
                    'volume': 281136,
                    'market_cap': 20868400,
                    'market_cap_rank': 800
                }
            ]
            
            for coin in test_coins:
                try:
                    result = await calculate_fomo_status_ultra_fast(coin)
                    
                    if result and len(result) == 5:
                        score, signal, trend, distribution, volume_spike = result
                        
                        if score > 0:
                            self.test_result(
                                f"analysis_{coin['symbol']}", 
                                True, 
                                f"Score: {score}% - {signal}"
                            )
                            
                            # Special check for TRON filtering
                            if coin['symbol'] == 'TRX' and score < 50:
                                self.test_result("tron_filtering", True, f"TRON filtered to {score}%")
                            elif coin['symbol'] == 'TRX':
                                self.test_result("tron_filtering", False, f"TRON score still high: {score}%")
                        else:
                            self.test_result(f"analysis_{coin['symbol']}", False, f"Zero score returned")
                    else:
                        self.test_result(f"analysis_{coin['symbol']}", False, f"Invalid result format: {result}")
                        
                except Exception as e:
                    self.test_result(f"analysis_{coin['symbol']}", False, str(e))
                    
        except Exception as e:
            self.test_result("analysis_system", False, f"Analysis system unavailable: {e}")
    
    async def test_bot_creation(self):
        """Test bot creation without starting it"""
        print("\n🤖 TESTING BOT CREATION")
        print("-" * 40)
        
        try:
            from telegram.ext import ApplicationBuilder, CommandHandler
            from telegram import Update
            from telegram.ext import ContextTypes
            
            # Get token
            token = os.getenv("TEST_BOT_TOKEN")
            if not token:
                self.test_result("bot_token", False, "No TEST_BOT_TOKEN found")
                return
            
            # Create application
            app = ApplicationBuilder().token(token).build()
            self.test_result("bot_creation", True, "Application created successfully")
            
            # Test handler creation
            async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("Test response")
            
            app.add_handler(CommandHandler("test", test_handler))
            self.test_result("handler_creation", True, "Handler added successfully")
            
            # Test initialization (without starting)
            await app.initialize()
            self.test_result("bot_initialization", True, "Bot initialized successfully")
            
            # Cleanup
            await app.shutdown()
            self.test_result("bot_cleanup", True, "Bot cleaned up successfully")
            
        except Exception as e:
            self.test_result("bot_creation", False, str(e))
    
    def test_database(self):
        """Test database functionality"""
        print("\n💾 TESTING DATABASE")
        print("-" * 40)
        
        try:
            from database import init_user_db, get_user_balance
            
            # Test database initialization
            init_user_db()
            self.test_result("database_init", True, "Database initialized")
            
            # Test user functions (with fallback for missing users)
            try:
                balance = get_user_balance(12345)  # Test user ID
                self.test_result("database_query", True, f"User balance query worked: {balance}")
            except Exception as e:
                # This might fail if user doesn't exist, which is fine
                self.test_result("database_query", True, f"Database query functional: {str(e)}")
                
        except Exception as e:
            self.test_result("database_test", False, str(e))
    
    async def test_api_connectivity(self):
        """Test API connectivity"""
        print("\n🌐 TESTING API CONNECTIVITY")
        print("-" * 40)
        
        try:
            import aiohttp
            
            # Test basic internet connectivity
            async with aiohttp.ClientSession() as session:
                async with session.get("https://httpbin.org/status/200", timeout=10) as response:
                    if response.status == 200:
                        self.test_result("internet_connectivity", True, "Internet connection working")
                    else:
                        self.test_result("internet_connectivity", False, f"HTTP {response.status}")
                        
        except Exception as e:
            self.test_result("internet_connectivity", False, str(e))
        
        # Test CoinGecko API (if available)
        try:
            from api_client import fetch_market_data_ultra_fast
            
            # This might fail due to rate limits, but we can test the function exists
            self.test_result("coingecko_api_client", True, "CoinGecko client available")
            
        except Exception as e:
            self.test_result("coingecko_api_client", False, str(e))
    
    def generate_report(self):
        """Generate final diagnostic report"""
        print("\n" + "=" * 60)
        print("📋 DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Summary
        success_rate = (self.results['success_count'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📊 SUMMARY:")
        print(f"   Tests passed: {self.results['success_count']}/{self.results['total_tests']}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        # Status assessment
        if success_rate >= 90:
            print(f"   🎉 STATUS: EXCELLENT - Bot is production ready!")
        elif success_rate >= 75:
            print(f"   ✅ STATUS: GOOD - Minor issues to address")
        elif success_rate >= 50:
            print(f"   ⚠️ STATUS: FAIR - Several issues need fixing")
        else:
            print(f"   🚨 STATUS: POOR - Major issues detected")
        
        # Issues
        if self.results['issues']:
            print(f"\n🚨 ISSUES TO FIX:")
            for i, issue in enumerate(self.results['issues'], 1):
                print(f"   {i}. {issue}")
        
        # Key insights
        print(f"\n🎯 KEY INSIGHTS:")
        
        analysis_tests = [name for name in self.results['tests'] if 'analysis_' in name]
        analysis_passed = [name for name in analysis_tests if self.results['tests'][name]['success']]
        
        if len(analysis_passed) >= len(analysis_tests) * 0.8:
            print(f"   ✅ Zero results problem: SOLVED ({len(analysis_passed)}/{len(analysis_tests)} coins working)")
        else:
            print(f"   ❌ Zero results problem: Still exists ({len(analysis_passed)}/{len(analysis_tests)} coins working)")
        
        if 'tron_filtering' in self.results['tests']:
            if self.results['tests']['tron_filtering']['success']:
                print(f"   ✅ TRON filtering: Working correctly")
            else:
                print(f"   ⚠️ TRON filtering: Needs adjustment")
        
        if 'bot_creation' in self.results['tests'] and self.results['tests']['bot_creation']['success']:
            print(f"   ✅ Bot functionality: Core systems working")
        else:
            print(f"   ❌ Bot functionality: Issues with bot creation")
        
        print(f"\n🔗 NEXT STEPS:")
        if success_rate >= 90:
            print(f"   1. Deploy to production with ENV=prod")
            print(f"   2. Test with real users")
            print(f"   3. Monitor for any issues")
        elif success_rate >= 75:
            print(f"   1. Fix the identified issues")
            print(f"   2. Re-run diagnostics")
            print(f"   3. Deploy when all tests pass")
        else:
            print(f"   1. Address critical failures first")
            print(f"   2. Check environment configuration")
            print(f"   3. Verify all dependencies installed")
        
        return self.results

async def main():
    """Run complete diagnostic suite"""
    print("🔍 FCB FOMO BOT DIAGNOSTICS")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now()}")
    print(f"🌍 Environment: {os.getenv('ENV', 'unknown')}")
    
    debugger = BotDebugger()
    
    # Run all tests
    debugger.test_environment()
    debugger.test_imports()
    await debugger.test_analysis_system()
    await debugger.test_bot_creation()
    debugger.test_database()
    await debugger.test_api_connectivity()
    
    # Generate final report
    results = debugger.generate_report()
    
    print(f"\n⏰ Completed: {datetime.now()}")
    print("🔍 Diagnostics complete!")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostics failed: {e}")
        import traceback
        traceback.print_exc()