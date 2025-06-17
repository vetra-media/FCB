"""
analysis_diagnostics.py - Complete Analysis System Diagnostics
Run this to identify exactly what's wrong with your analysis system

USAGE:
    python analysis_diagnostics.py

This will:
1. Test all import chains
2. Identify circular dependencies
3. Test with real coin data
4. Show you exactly where the zero results are coming from
5. Provide specific fixes
"""

import asyncio
import logging
import traceback
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data that mimics real CoinGecko responses
TEST_COINS = {
    'bitcoin': {
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
    'tron': {
        'id': 'tron',
        'symbol': 'TRX', 
        'name': 'TRON',
        'current_price': 0.102456,
        'price_change_percentage_1h_in_currency': 1.85,
        'price_change_percentage_24h_in_currency': 12.75,  # This was causing issues
        'total_volume': 281000000,  # This was the issue volume
        'market_cap': 26000000000,  # $26B market cap
        'market_cap_rank': 15
    },
    'small_cap': {
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
}

def normalize_coin_data(coin_data: Dict) -> Dict:
    """
    Convert CoinGecko format to your analysis format
    """
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

class AnalysisDiagnostics:
    """
    Complete diagnostics for the analysis system
    """
    
    def __init__(self):
        self.test_results = {}
        self.import_results = {}
        self.function_results = {}
        
    async def run_complete_diagnostics(self):
        """
        Run complete diagnostic suite
        """
        print("🔍 STARTING COMPLETE CFB ANALYSIS DIAGNOSTICS")
        print("=" * 60)
        
        # Step 1: Test imports
        await self.test_imports()
        
        # Step 2: Test individual modules
        await self.test_individual_modules()
        
        # Step 3: Test main analysis functions
        await self.test_main_analysis_functions()
        
        # Step 4: Test with problematic coins
        await self.test_problematic_scenarios()
        
        # Step 5: Generate report
        self.generate_diagnostic_report()
    
    async def test_imports(self):
        """
        Test all import chains to identify circular dependencies
        """
        print("\n📦 TESTING IMPORTS")
        print("-" * 30)
        
        # Test each module individually
        modules_to_test = [
            'legacy',
            'core_enhanced', 
            'patterns',
            'elite_engine',
            'catalyst_engine',
            'integration'
        ]
        
        for module_name in modules_to_test:
            try:
                print(f"🔄 Testing analysis.{module_name}...")
                
                if module_name == 'legacy':
                    from analysis.legacy import calculate_fomo_status
                    self.import_results[module_name] = "✅ SUCCESS"
                    
                elif module_name == 'core_enhanced':
                    from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
                    self.import_results[module_name] = "✅ SUCCESS"
                    
                elif module_name == 'patterns':
                    from analysis.patterns import calculate_fomo_status_ultra_fast_enhanced
                    self.import_results[module_name] = "✅ SUCCESS"
                    
                elif module_name == 'elite_engine':
                    from analysis.elite_engine import get_gaming_fomo_score
                    self.import_results[module_name] = "✅ SUCCESS"
                    
                elif module_name == 'catalyst_engine':
                    from analysis.catalyst_engine import analyze_coin_catalysts
                    self.import_results[module_name] = "✅ SUCCESS"
                    
                elif module_name == 'integration':
                    from analysis.integration import analyze_coin_comprehensive
                    self.import_results[module_name] = "✅ SUCCESS"
                
                print(f"   ✅ {module_name} imported successfully")
                
            except ImportError as e:
                self.import_results[module_name] = f"❌ IMPORT ERROR: {str(e)}"
                print(f"   ❌ {module_name} failed: {e}")
                
            except Exception as e:
                self.import_results[module_name] = f"❌ ERROR: {str(e)}"
                print(f"   ❌ {module_name} error: {e}")
        
        # Test main __init__.py
        try:
            print(f"🔄 Testing analysis.__init__...")
            from analysis import calculate_fomo_status_ultra_fast
            self.import_results['__init__'] = "✅ SUCCESS"
            print(f"   ✅ analysis.__init__ imported successfully")
        except Exception as e:
            self.import_results['__init__'] = f"❌ ERROR: {str(e)}"
            print(f"   ❌ analysis.__init__ failed: {e}")
    
    async def test_individual_modules(self):
        """
        Test each module with real data
        """
        print("\n🧪 TESTING INDIVIDUAL MODULES")
        print("-" * 40)
        
        test_coin = normalize_coin_data(TEST_COINS['bitcoin'])
        
        # Test legacy module
        try:
            print("🔄 Testing legacy module...")
            from analysis.legacy import calculate_fomo_status
            
            result = calculate_fomo_status(test_coin)
            if result and len(result) >= 4:
                score = result[0] if isinstance(result[0], (int, float)) else 0
                print(f"   ✅ Legacy result: {score}% - {result[1] if len(result) > 1 else 'No signal'}")
                self.function_results['legacy'] = f"✅ Score: {score}%"
            else:
                print(f"   ⚠️ Legacy returned unexpected format: {result}")
                self.function_results['legacy'] = f"⚠️ Unexpected format: {result}"
                
        except Exception as e:
            print(f"   ❌ Legacy failed: {e}")
            self.function_results['legacy'] = f"❌ Error: {str(e)}"
        
        # Test core enhanced
        try:
            print("🔄 Testing core enhanced module...")
            from analysis.core_enhanced import calculate_fomo_status_ultra_fast_v21
            
            result = await calculate_fomo_status_ultra_fast_v21(test_coin)
            if result and len(result) == 5:
                score = result[0]
                print(f"   ✅ Core enhanced result: {score}% - {result[1]}")
                self.function_results['core_enhanced'] = f"✅ Score: {score}%"
            else:
                print(f"   ⚠️ Core enhanced unexpected format: {result}")
                self.function_results['core_enhanced'] = f"⚠️ Unexpected format: {result}"
                
        except Exception as e:
            print(f"   ❌ Core enhanced failed: {e}")
            self.function_results['core_enhanced'] = f"❌ Error: {str(e)}"
        
        # Test elite engine
        try:
            print("🔄 Testing elite engine...")
            from analysis.elite_engine import get_gaming_fomo_score
            
            result = await get_gaming_fomo_score(test_coin)
            if result and 'score' in result:
                score = result['score']
                print(f"   ✅ Elite gaming result: {score}% - {result.get('signal', 'No signal')}")
                self.function_results['elite_gaming'] = f"✅ Score: {score}%"
            else:
                print(f"   ⚠️ Elite gaming unexpected format: {result}")
                self.function_results['elite_gaming'] = f"⚠️ Unexpected format: {result}"
                
        except Exception as e:
            print(f"   ❌ Elite gaming failed: {e}")
            self.function_results['elite_gaming'] = f"❌ Error: {str(e)}"
    
    async def test_main_analysis_functions(self):
        """
        Test the main analysis functions your bot uses
        """
        print("\n🎯 TESTING MAIN ANALYSIS FUNCTIONS")
        print("-" * 45)
        
        test_coin = normalize_coin_data(TEST_COINS['bitcoin'])
        
        # Test main analysis function
        try:
            print("🔄 Testing calculate_fomo_status_ultra_fast...")
            from analysis import calculate_fomo_status_ultra_fast
            
            result = await calculate_fomo_status_ultra_fast(test_coin)
            if result and len(result) == 5:
                score, signal, trend, distribution, volume_spike = result
                print(f"   ✅ Main analysis: {score}% - {signal}")
                print(f"   📊 Details: Trend={trend[:50]}...")
                print(f"   💧 Volume spike: {volume_spike:.1f}x")
                self.function_results['main_analysis'] = f"✅ Score: {score}%"
                
                # This is the key test - check if score is zero
                if score == 0:
                    print(f"   🚨 ZERO SCORE DETECTED - This is your problem!")
                    self.function_results['zero_score_issue'] = "🚨 CONFIRMED"
                else:
                    print(f"   ✅ Non-zero score: {score}%")
                    self.function_results['zero_score_issue'] = "✅ No issue"
                    
            else:
                print(f"   ❌ Main analysis unexpected format: {result}")
                self.function_results['main_analysis'] = f"❌ Unexpected format: {result}"
                
        except Exception as e:
            print(f"   ❌ Main analysis failed: {e}")
            print(f"   📋 Traceback: {traceback.format_exc()}")
            self.function_results['main_analysis'] = f"❌ Error: {str(e)}"
    
    async def test_problematic_scenarios(self):
        """
        Test with the specific coins that were causing issues
        """
        print("\n🚨 TESTING PROBLEMATIC SCENARIOS")
        print("-" * 45)
        
        # Test TRON (the $26B problem)
        print("🔄 Testing TRON scenario (the $26B issue)...")
        tron_coin = normalize_coin_data(TEST_COINS['tron'])
        
        try:
            from analysis import calculate_fomo_status_ultra_fast
            result = await calculate_fomo_status_ultra_fast(tron_coin)
            
            if result and len(result) == 5:
                score = result[0]
                print(f"   📊 TRON result: {score}% - {result[1]}")
                
                # Check if fixes are working
                if score < 40:  # Should be filtered down from original 85%
                    print(f"   ✅ TRON fix working: Score reduced to {score}%")
                    self.test_results['tron_fix'] = "✅ Working"
                else:
                    print(f"   ⚠️ TRON fix may not be working: Score still {score}%")
                    self.test_results['tron_fix'] = f"⚠️ Score: {score}%"
            else:
                print(f"   ❌ TRON test failed: {result}")
                self.test_results['tron_fix'] = f"❌ Failed: {result}"
                
        except Exception as e:
            print(f"   ❌ TRON test error: {e}")
            self.test_results['tron_fix'] = f"❌ Error: {str(e)}"
        
        # Test small cap coin (Derive-like)
        print("🔄 Testing small cap scenario (Derive-like)...")
        small_cap = normalize_coin_data(TEST_COINS['small_cap'])
        
        try:
            result = await calculate_fomo_status_ultra_fast(small_cap)
            
            if result and len(result) == 5:
                score = result[0]
                print(f"   📊 Small cap result: {score}% - {result[1]}")
                
                if score >= 60:  # Should be boosted for good opportunities
                    print(f"   ✅ Small cap boost working: Score {score}%")
                    self.test_results['small_cap_boost'] = "✅ Working"
                else:
                    print(f"   📊 Small cap score: {score}% (may need tuning)")
                    self.test_results['small_cap_boost'] = f"📊 Score: {score}%"
            else:
                print(f"   ❌ Small cap test failed: {result}")
                self.test_results['small_cap_boost'] = f"❌ Failed: {result}"
                
        except Exception as e:
            print(f"   ❌ Small cap test error: {e}")
            self.test_results['small_cap_boost'] = f"❌ Error: {str(e)}"
    
    def generate_diagnostic_report(self):
        """
        Generate comprehensive diagnostic report
        """
        print("\n📋 DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Import status
        print("\n📦 IMPORT STATUS:")
        for module, status in self.import_results.items():
            print(f"   {module}: {status}")
        
        # Function test status  
        print("\n🔧 FUNCTION TEST STATUS:")
        for func, status in self.function_results.items():
            print(f"   {func}: {status}")
        
        # Issue analysis
        print("\n🚨 ISSUE ANALYSIS:")
        
        # Check for zero score issue
        if self.function_results.get('zero_score_issue') == "🚨 CONFIRMED":
            print("   🎯 ZERO SCORE ISSUE CONFIRMED")
            print("      - Your analysis is returning 0% scores")
            print("      - This causes blank results in your bot")
            print("      - Fix: Use the bulletproof analysis/__init__.py provided")
            
        # Check import issues
        failed_imports = [name for name, status in self.import_results.items() if "❌" in status]
        if failed_imports:
            print(f"   📦 IMPORT ISSUES: {', '.join(failed_imports)}")
            print("      - Some analysis modules failed to import")
            print("      - This reduces available analysis features")
            print("      - Fix: Check dependencies and circular imports")
        
        # Check function issues
        failed_functions = [name for name, status in self.function_results.items() if "❌" in status]
        if failed_functions:
            print(f"   🔧 FUNCTION ISSUES: {', '.join(failed_functions)}")
            print("      - Some analysis functions are failing")
            print("      - This causes inconsistent results")
            print("      - Fix: Add error handling and fallbacks")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if self.function_results.get('zero_score_issue') == "🚨 CONFIRMED":
            print("   1. 🔧 IMMEDIATE FIX:")
            print("      - Replace your analysis/__init__.py with the bulletproof version")
            print("      - This will eliminate zero results permanently")
            print("      - Gaming fallbacks will ensure engaging results always")
        
        if failed_imports:
            print("   2. 📦 IMPORT FIXES:")
            print("      - Check for circular import dependencies")
            print("      - Use safe import patterns with try/except")
            print("      - Consider lazy loading for complex modules")
        
        print("   3. 🛡️ BULLETPROOF STRATEGY:")
        print("      - Always have a gaming fallback that never fails")
        print("      - Isolate advanced features with error boundaries")
        print("      - Ensure main analysis function always returns results")
        
        print("   4. 🎮 GAMING FOCUS:")
        print("      - Prioritize entertaining results over perfect analysis")
        print("      - Users prefer engaging content over blank screens")
        print("      - Advanced features are bonuses, not requirements")
        
        # Summary
        total_imports = len(self.import_results)
        successful_imports = len([s for s in self.import_results.values() if "✅" in s])
        total_functions = len(self.function_results)
        successful_functions = len([s for s in self.function_results.values() if "✅" in s])
        
        print(f"\n📊 SUMMARY:")
        print(f"   📦 Imports: {successful_imports}/{total_imports} successful")
        print(f"   🔧 Functions: {successful_functions}/{total_functions} working")
        
        if successful_functions >= total_functions * 0.7:
            print(f"   🎯 STATUS: MOSTLY WORKING - Apply bulletproof fixes")
        elif successful_functions >= total_functions * 0.5:
            print(f"   ⚠️ STATUS: PARTIAL ISSUES - Needs attention")
        else:
            print(f"   🚨 STATUS: MAJOR ISSUES - Significant fixes needed")
        
        print("\n✅ DIAGNOSTIC COMPLETE")
        print("📋 Use this report to fix your analysis system!")

async def main():
    """
    Run complete diagnostics
    """
    diagnostics = AnalysisDiagnostics()
    await diagnostics.run_complete_diagnostics()

if __name__ == "__main__":
    # Make sure we can import the analysis module
    try:
        # Add current directory to path so we can import analysis
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Run diagnostics
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️ Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostics failed to run: {e}")
        print(f"📋 Error details: {traceback.format_exc()}")
        print("\n💡 This usually means:")
        print("   - analysis module is not in the correct location")
        print("   - Python path is not set correctly")
        print("   - Dependencies are missing")
        print(f"   - Current directory: {os.getcwd()}")
        print(f"   - Python path: {sys.path[:3]}...")