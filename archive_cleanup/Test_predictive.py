"""
Test script for predictive algorithm
Run this to verify everything works before going live
"""

import asyncio
import sys
import os

# Add your project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your modules
from analysis import test_predictive_vs_original

async def main():
    print("🚀 TESTING PREDICTIVE ALGORITHM INTEGRATION")
    print("=" * 60)
    
    await test_predictive_vs_original()
    
    print("\n🎯 Integration test complete!")
    print("If no errors above, your integration is successful!")

if __name__ == "__main__":
    asyncio.run(main())