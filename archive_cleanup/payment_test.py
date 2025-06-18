#!/usr/bin/env python3
"""
Mock payment flow test
Simulates the payment success handler without real payments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_user_db,
    get_user_balance_detailed,
    add_fcb_tokens,
    get_db_connection
)

def simulate_payment_success(user_id, package_key="starter"):
    """Simulate a successful payment"""
    
    print(f"🧪 Simulating payment for user {user_id}")
    print("=" * 50)
    
    # Mock package data (from your config)
    FCB_STAR_PACKAGES = {
        'starter': {'tokens': 10, 'stars': 100, 'title': 'Starter Pack'},
        'pro': {'tokens': 100, 'stars': 900, 'title': 'Pro Pack'},
        'whale': {'tokens': 1000, 'stars': 8000, 'title': 'Whale Pack'},
    }
    
    if package_key not in FCB_STAR_PACKAGES:
        print(f"❌ Invalid package key: {package_key}")
        return False
    
    package = FCB_STAR_PACKAGES[package_key]
    tokens = package['tokens']
    stars = package['stars']
    
    print(f"📦 Package: {package['title']}")
    print(f"💎 Tokens: {tokens}")
    print(f"⭐ Stars: {stars}")
    
    # Check balance before
    print(f"\n📊 Balance BEFORE payment:")
    balance_before = get_user_balance_detailed(user_id)
    if balance_before:
        print(f"   FCB Balance: {balance_before['fcb_balance']}")
        print(f"   Total Queries: {balance_before['total_queries']}")
        print(f"   First Purchase: {balance_before['first_purchase_date']}")
    
    # Simulate payment processing
    print(f"\n💳 Processing payment...")
    
    # Add tokens (this is the core payment logic)
    success, new_balance = add_fcb_tokens(user_id, tokens)
    
    if success:
        # Record first purchase date (simulate the payment handler)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET first_purchase_date = CURRENT_TIMESTAMP 
                    WHERE user_id = ? AND first_purchase_date IS NULL
                ''', (user_id,))
                conn.commit()
                print(f"✅ First purchase date updated")
        except Exception as e:
            print(f"⚠️ Could not update first purchase date: {e}")
        
        print(f"✅ Payment successful! New FCB balance: {new_balance}")
        
        # Check balance after
        print(f"\n📊 Balance AFTER payment:")
        balance_after = get_user_balance_detailed(user_id)
        if balance_after:
            print(f"   FCB Balance: {balance_after['fcb_balance']}")
            print(f"   Total Queries: {balance_after['total_queries']}")
            print(f"   First Purchase: {balance_after['first_purchase_date']}")
            
            # Verify the increase
            tokens_added = balance_after['fcb_balance'] - (balance_before['fcb_balance'] if balance_before else 0)
            print(f"\n🎯 Verification:")
            print(f"   Expected tokens added: {tokens}")
            print(f"   Actual tokens added: {tokens_added}")
            print(f"   ✅ Match: {tokens == tokens_added}")
        
        return True
    else:
        print(f"❌ Payment failed!")
        return False

def test_multiple_purchases():
    """Test multiple purchases for the same user"""
    
    print("\n🔄 Testing multiple purchases...")
    test_user_id = 99999
    
    # First purchase
    print("\n--- First Purchase ---")
    simulate_payment_success(test_user_id, "starter")
    
    # Second purchase
    print("\n--- Second Purchase ---")
    simulate_payment_success(test_user_id, "pro")
    
    # Third purchase
    print("\n--- Third Purchase ---")
    simulate_payment_success(test_user_id, "whale")
    
    # Final summary
    print("\n📋 Final Summary:")
    final_balance = get_user_balance_detailed(test_user_id)
    if final_balance:
        print(f"   Final FCB Balance: {final_balance['fcb_balance']}")
        print(f"   Expected: {10 + 100 + 1000} = 1110")
        print(f"   ✅ Correct: {final_balance['fcb_balance'] == 1110}")

if __name__ == "__main__":
    # Initialize database
    init_user_db()
    
    # Test single payment
    simulate_payment_success(12345, "pro")
    
    # Test multiple payments
    test_multiple_purchases()
    
    print(f"\n🎉 Payment flow testing complete!")