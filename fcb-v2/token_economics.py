"""
FCB v2 Token Economics Database System - WITH COMPLETE DEBUG SYSTEM
Complete recreation of FCB v1's sophisticated token and rate limiting system
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Tuple, Dict, Any, Optional
from threading import Lock

# =============================================================================
# TOKEN ECONOMICS CONSTANTS
# =============================================================================

# Daily limits (recreated from FCB v1)
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# FCB Token packages (Telegram Stars integration)
FCB_STAR_PACKAGES = {
    'starter': {
        'stars': 100,
        'tokens': 100,
        'title': 'Starter Pack - 100 FCB Tokens',
        'description': '100 premium crypto scans'
    },
    'premium': {
        'stars': 250,
        'tokens': 250,
        'title': 'Premium Pack - 250 FCB Tokens',
        'description': '250 premium crypto scans + priority support'
    },
    'pro': {
        'stars': 500,
        'tokens': 500,
        'title': 'Pro Pack - 500 FCB Tokens',
        'description': '500 premium crypto scans + advanced features'
    },
    'elite': {
        'stars': 1000,
        'tokens': 1000,
        'title': 'Elite Pack - 1000 FCB Tokens',
        'description': '1000 premium crypto scans + VIP access'
    }
}

# Rate limiting constants
RATE_LIMIT_WINDOW = 1.0  # 1 second between requests

# =============================================================================
# DATABASE CONNECTION MANAGEMENT
# =============================================================================

class DatabaseManager:
    def __init__(self, db_path: str = 'fcb_v2.db'):
        self.db_path = db_path
        self.lock = Lock()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def init_database(self):
        """Initialize database tables for token economics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table for token economics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    fcb_balance INTEGER DEFAULT 0,
                    free_queries_used INTEGER DEFAULT 0,
                    new_user_bonus_used INTEGER DEFAULT 0,
                    last_free_query_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_purchase_date TIMESTAMP NULL,
                    total_tokens_purchased INTEGER DEFAULT 0,
                    total_tokens_spent INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    last_request_time REAL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Token transactions table (for audit trail)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_type TEXT,
                    amount INTEGER,
                    balance_before INTEGER,
                    balance_after INTEGER,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            logging.info("💾 FCB v2 token economics database initialized")

# Global database manager instance
db_manager = DatabaseManager()

# =============================================================================
# USER BALANCE MANAGEMENT
# =============================================================================

def get_user_balance(user_id: int) -> Tuple[int, int, int, int, bool]:
    """
    Get comprehensive user balance information
    
    Returns:
        (fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus)
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get or create user record
        cursor.execute('''
            SELECT fcb_balance, free_queries_used, new_user_bonus_used, 
                   last_free_query_date, first_purchase_date, created_at
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            # Initialize new user with bonus scans
            cursor.execute('''
                INSERT INTO users (user_id, fcb_balance, free_queries_used, new_user_bonus_used, last_free_query_date)
                VALUES (?, 0, 0, 0, ?)
            ''', (user_id, datetime.now().date().isoformat()))
            conn.commit()
            
            logging.info(f"👤 New user {user_id} initialized with {NEW_USER_BONUS} bonus scans")
            return 0, 0, 0, NEW_USER_BONUS + FREE_QUERIES_PER_DAY, False
        
        # Check if daily queries need reset
        fcb_balance = user_data['fcb_balance']
        free_queries_used = user_data['free_queries_used']
        new_user_bonus_used = user_data['new_user_bonus_used']
        last_query_date = user_data['last_free_query_date']
        has_received_bonus = user_data['first_purchase_date'] is not None
        
        # Reset daily queries if new day
        today = datetime.now().date().isoformat()
        if last_query_date != today:
            cursor.execute('''
                UPDATE users SET free_queries_used = 0, last_free_query_date = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (today, user_id))
            conn.commit()
            free_queries_used = 0
            logging.info(f"🔄 Daily queries reset for user {user_id}")
        
        # Calculate remaining free queries
        remaining_new_user_bonus = max(0, NEW_USER_BONUS - new_user_bonus_used)
        remaining_daily_queries = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
        total_free_remaining = remaining_daily_queries + remaining_new_user_bonus
        
        return fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus

def get_user_balance_detailed(user_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed balance information for debugging/admin purposes"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
        
        # Convert to dict and calculate additional fields
        result = dict(user_data)
        
        # Calculate totals
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        result.update({
            'total_free_remaining': total_free_remaining,
            'has_received_bonus': has_received_bonus,
            'total_queries': result['total_tokens_spent'] + free_queries_used + new_user_bonus_used
        })
        
        return result

# =============================================================================
# TOKEN SPENDING AND EARNING
# =============================================================================

def spend_fcb_token(user_id: int, description: str = "API query") -> Tuple[bool, str]:
    """
    Spend one FCB token or free query
    
    Returns:
        (success, message)
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get current balance
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, _ = get_user_balance(user_id)
        
        if total_free_remaining <= 0 and fcb_balance <= 0:
            return False, "❌ No queries available! Use /buy to get more FCB tokens."
        
        # Determine what to spend (priority: daily free -> new user bonus -> FCB tokens)
        today = datetime.now().date().isoformat()
        
        if free_queries_used < FREE_QUERIES_PER_DAY:
            # Spend daily free query
            cursor.execute('''
                UPDATE users SET free_queries_used = free_queries_used + 1, 
                                last_free_query_date = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (today, user_id))
            
            # Log transaction
            cursor.execute('''
                INSERT INTO token_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
                VALUES (?, 'spend_daily_free', 1, ?, ?, ?)
            ''', (user_id, fcb_balance, fcb_balance, description))
            
            conn.commit()
            remaining = FREE_QUERIES_PER_DAY - (free_queries_used + 1)
            logging.info(f"💸 User {user_id}: Spent daily free query ({remaining} daily remaining)")
            return True, f"✅ Used daily free scan ({remaining} daily scans remaining)"
            
        elif new_user_bonus_used < NEW_USER_BONUS:
            # Spend new user bonus
            cursor.execute('''
                UPDATE users SET new_user_bonus_used = new_user_bonus_used + 1, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            # Log transaction
            cursor.execute('''
                INSERT INTO token_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
                VALUES (?, 'spend_bonus', 1, ?, ?, ?)
            ''', (user_id, fcb_balance, fcb_balance, description))
            
            conn.commit()
            remaining = NEW_USER_BONUS - (new_user_bonus_used + 1)
            logging.info(f"💸 User {user_id}: Spent new user bonus ({remaining} bonus remaining)")
            return True, f"✅ Used bonus scan ({remaining} bonus scans remaining)"
            
        elif fcb_balance > 0:
            # Spend FCB token
            new_balance = fcb_balance - 1
            cursor.execute('''
                UPDATE users SET fcb_balance = ?, total_tokens_spent = total_tokens_spent + 1, 
                                last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_balance, user_id))
            
            # Log transaction
            cursor.execute('''
                INSERT INTO token_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
                VALUES (?, 'spend_fcb', 1, ?, ?, ?)
            ''', (user_id, fcb_balance, new_balance, description))
            
            conn.commit()
            logging.info(f"💸 User {user_id}: Spent 1 FCB token ({new_balance} remaining)")
            return True, f"✅ Used 1 FCB token ({new_balance} tokens remaining)"
        
        return False, "❌ Unexpected error in token spending"

def add_fcb_tokens(user_id: int, amount: int, description: str = "Purchase") -> Tuple[bool, int]:
    """
    Add FCB tokens to user's balance
    
    Returns:
        (success, new_balance)
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get current balance
        current_balance = get_user_balance(user_id)[0]  # fcb_balance
        new_balance = current_balance + amount
        
        # Update balance
        cursor.execute('''
            UPDATE users SET fcb_balance = ?, total_tokens_purchased = total_tokens_purchased + ?, 
                            last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (new_balance, amount, user_id))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO token_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
            VALUES (?, 'add_fcb', ?, ?, ?, ?)
        ''', (user_id, amount, current_balance, new_balance, description))
        
        conn.commit()
        
        logging.info(f"💰 User {user_id}: Added {amount} FCB tokens (balance: {current_balance} → {new_balance})")
        return True, new_balance

# =============================================================================
# RATE LIMITING SYSTEM
# =============================================================================

def check_rate_limit_with_fcb(user_id: int) -> Tuple[bool, float, str]:
    """
    Check if user can make a request (rate limit + token balance)
    
    Returns:
        (allowed, time_remaining, reason)
    """
    # First check token/query availability
    fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
    
    if total_free_remaining <= 0 and fcb_balance <= 0:
        return False, 0, "No queries available"
    
    # Check rate limiting
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        current_time = time.time()
        
        # Get last request time
        cursor.execute('''
            SELECT last_request_time FROM rate_limits WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            last_request_time = result['last_request_time']
            time_since_last = current_time - last_request_time
            
            if time_since_last < RATE_LIMIT_WINDOW:
                time_remaining = RATE_LIMIT_WINDOW - time_since_last
                return False, time_remaining, "Rate limited"
        
        # Update last request time
        cursor.execute('''
            INSERT OR REPLACE INTO rate_limits (user_id, last_request_time)
            VALUES (?, ?)
        ''', (user_id, current_time))
        
        conn.commit()
        
        return True, 0, "Allowed"

def update_user_activity(user_id: int):
    """Update user's last activity timestamp"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

# =============================================================================
# PURCHASE MANAGEMENT
# =============================================================================

def record_purchase(user_id: int, package_key: str, stars_amount: int, tokens_amount: int) -> bool:
    """Record a successful token purchase"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Add tokens to balance
            success, new_balance = add_fcb_tokens(user_id, tokens_amount, f"Purchase: {package_key}")
            
            if not success:
                return False
            
            # Update first purchase date if this is their first purchase
            cursor.execute('''
                UPDATE users 
                SET first_purchase_date = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND first_purchase_date IS NULL
            ''', (user_id,))
            
            conn.commit()
            
            logging.info(f"🛒 User {user_id}: Purchase recorded - {package_key} ({stars_amount} stars → {tokens_amount} tokens)")
            return True
            
        except Exception as e:
            logging.error(f"❌ Purchase recording failed for user {user_id}: {e}")
            return False

# =============================================================================
# ANALYTICS AND REPORTING
# =============================================================================

def get_user_statistics(user_id: int) -> Dict[str, Any]:
    """Get comprehensive user statistics"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get user data
        user_data = get_user_balance_detailed(user_id)
        if not user_data:
            return {}
        
        # Get transaction history
        cursor.execute('''
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM token_transactions 
            WHERE user_id = ?
            GROUP BY transaction_type
        ''', (user_id,))
        
        transactions = {row['transaction_type']: {'count': row['count'], 'total': row['total']} 
                       for row in cursor.fetchall()}
        
        return {
            'user_data': user_data,
            'transactions': transactions,
            'efficiency': {
                'tokens_per_day': user_data.get('total_tokens_spent', 0) / max(1, 
                    (datetime.now() - datetime.fromisoformat(user_data.get('created_at', '2025-01-01'))).days),
                'purchase_ratio': user_data.get('total_tokens_purchased', 0) / max(1, user_data.get('total_tokens_spent', 1))
            }
        }

def get_system_statistics() -> Dict[str, Any]:
    """Get system-wide token economics statistics"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # User counts
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as active_users FROM users WHERE last_activity > datetime("now", "-24 hours")')
        active_users = cursor.fetchone()['active_users']
        
        # Token statistics
        cursor.execute('SELECT SUM(fcb_balance) as total_balance, SUM(total_tokens_purchased) as total_purchased, SUM(total_tokens_spent) as total_spent FROM users')
        token_stats = cursor.fetchone()
        
        # Revenue (approximate based on packages)
        cursor.execute('''
            SELECT description, COUNT(*) as count 
            FROM token_transactions 
            WHERE transaction_type = 'add_fcb' AND description LIKE 'Purchase:%'
            GROUP BY description
        ''')
        
        revenue_data = cursor.fetchall()
        
        return {
            'users': {
                'total': total_users,
                'active_24h': active_users,
                'retention_rate': (active_users / max(total_users, 1)) * 100
            },
            'tokens': {
                'total_balance': token_stats['total_balance'] or 0,
                'total_purchased': token_stats['total_purchased'] or 0,
                'total_spent': token_stats['total_spent'] or 0,
                'utilization_rate': ((token_stats['total_spent'] or 0) / max(token_stats['total_purchased'] or 1, 1)) * 100
            },
            'revenue': dict(revenue_data)
        }

# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def get_user_balance_info(user_id: int) -> Dict[str, Any]:
    """Get user balance info formatted for integration with session_manager"""
    fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
    
    return {
        'fcb_balance': fcb_balance,
        'free_queries_used': free_queries_used,
        'new_user_bonus_used': new_user_bonus_used,
        'total_free_remaining': total_free_remaining,
        'has_received_bonus': has_received_bonus,
        'total_scans': fcb_balance + total_free_remaining
    }

def get_clean_balance_display(user_id: int) -> str:
    """Get simple, clean balance display for UI"""
    try:
        balance_info = get_user_balance_info(user_id)
        total_scans = balance_info['total_scans']
        return f"🤖 <i>Scans: {total_scans}</i>"
    except Exception as e:
        logging.error(f"Error getting clean balance: {e}")
        return "🤖 <i>Scans: Error</i>"

# =============================================================================
# DEBUG AND TESTING FUNCTIONS - COMPLETE IMPLEMENTATION
# =============================================================================

def debug_user_balance(user_id: int):
    """Debug function to check user balance issues"""
    try:
        print(f"\n=== DEBUG USER BALANCE for {user_id} ===")
        
        # Test database connection
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                print(f"✅ User found in database:")
                for key in user_data.keys():
                    print(f"  {key}: {user_data[key]}")
            else:
                print(f"❌ User NOT found in database - will be created on first query")
            
            # Test balance calculation
            balance_info = get_user_balance_info(user_id)
            print(f"\n📊 Calculated Balance:")
            for key, value in balance_info.items():
                print(f"  {key}: {value}")
            
            # Test today's date logic
            today = datetime.now().date().isoformat()
            print(f"\n📅 Today's date: {today}")
            
            if user_data:
                last_query_date = user_data['last_free_query_date']
                print(f"📅 Last query date: {last_query_date}")
                print(f"📅 Dates match: {last_query_date == today}")
            
            # Test raw balance calculation
            print(f"\n🔬 Raw Balance Calculation:")
            fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
            print(f"  fcb_balance: {fcb_balance}")
            print(f"  free_queries_used: {free_queries_used}")
            print(f"  new_user_bonus_used: {new_user_bonus_used}")
            print(f"  total_free_remaining: {total_free_remaining}")
            print(f"  has_received_bonus: {has_received_bonus}")
            
            remaining_new_user_bonus = max(0, NEW_USER_BONUS - new_user_bonus_used)
            remaining_daily_queries = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
            print(f"  remaining_new_user_bonus: {remaining_new_user_bonus}")
            print(f"  remaining_daily_queries: {remaining_daily_queries}")
            print(f"  total_calculated: {remaining_daily_queries + remaining_new_user_bonus}")
            
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

def test_user_balance():
    """Test function to verify token economics"""
    test_user_id = 12345  # Use a test user ID
    
    print("🧪 Testing token economics...")
    
    # Test 1: New user initialization
    debug_user_balance(test_user_id)
    
    # Test 2: Balance check
    balance_info = get_user_balance_info(test_user_id)
    print(f"\n🔋 Balance for new user: {balance_info}")
    
    # Test 3: Rate limit check
    allowed, time_remaining, reason = check_rate_limit_with_fcb(test_user_id)
    print(f"\n⏱️ Rate limit check: allowed={allowed}, reason={reason}")
    
    if balance_info['total_scans'] <= 0:
        print("\n❌ PROBLEM: New user has 0 scans!")
        print("Expected: 8 scans (5 daily + 3 bonus)")
    else:
        print(f"\n✅ User has {balance_info['total_scans']} scans available")
    
    # Test 4: Database integrity
    print(f"\n🔧 Database Integrity Check:")
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"  Tables found: {tables}")
            
            # Check constants
            print(f"  FREE_QUERIES_PER_DAY: {FREE_QUERIES_PER_DAY}")
            print(f"  NEW_USER_BONUS: {NEW_USER_BONUS}")
            
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")

def ensure_user_has_scans(user_id: int):
    """Emergency function to ensure user has scans"""
    try:
        balance_info = get_user_balance_info(user_id)
        
        if balance_info['total_scans'] <= 0:
            print(f"🚨 User {user_id} has 0 scans, adding emergency scans...")
            
            # Add emergency scans
            success, new_balance = add_fcb_tokens(user_id, 10, "Emergency scans - debug")
            
            if success:
                print(f"✅ Added 10 emergency scans to user {user_id}")
                return True
            else:
                print(f"❌ Failed to add emergency scans")
                return False
        else:
            print(f"✅ User {user_id} already has {balance_info['total_scans']} scans")
            return True
            
    except Exception as e:
        print(f"❌ Error ensuring user has scans: {e}")
        return False

def force_user_initialization(user_id: int):
    """Force proper user initialization with all bonus scans"""
    try:
        print(f"🔧 Force initializing user {user_id}...")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                print(f"  User exists, checking balance...")
                balance_info = get_user_balance_info(user_id)
                if balance_info['total_scans'] <= 0:
                    print(f"  User has 0 scans, resetting...")
                    # Reset user to fresh state
                    today = datetime.now().date().isoformat()
                    cursor.execute('''
                        UPDATE users SET 
                            free_queries_used = 0, 
                            new_user_bonus_used = 0,
                            last_free_query_date = ?
                        WHERE user_id = ?
                    ''', (today, user_id))
                    conn.commit()
                    print(f"  ✅ Reset user to fresh state")
                else:
                    print(f"  ✅ User already has {balance_info['total_scans']} scans")
            else:
                print(f"  Creating new user...")
                today = datetime.now().date().isoformat()
                cursor.execute('''
                    INSERT INTO users (user_id, fcb_balance, free_queries_used, new_user_bonus_used, last_free_query_date)
                    VALUES (?, 0, 0, 0, ?)
                ''', (user_id, today))
                conn.commit()
                print(f"  ✅ Created new user")
        
        # Verify the result
        balance_info = get_user_balance_info(user_id)
        print(f"  📊 Final balance: {balance_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Force initialization failed: {e}")
        return False

def run_complete_debug_test(user_id: int = None):
    """Run complete debug test for token economics"""
    if user_id is None:
        user_id = 999999  # Test user
    
    print("🔧" + "="*50)
    print("🔧 COMPLETE FCB TOKEN ECONOMICS DEBUG TEST")
    print("🔧" + "="*50)
    
    # Test 1: Database connection
    print("\n📊 Test 1: Database Connection")
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return
    
    # Test 2: Constants
    print("\n📊 Test 2: Constants Check")
    print(f"✅ FREE_QUERIES_PER_DAY: {FREE_QUERIES_PER_DAY}")
    print(f"✅ NEW_USER_BONUS: {NEW_USER_BONUS}")
    print(f"✅ Expected total for new user: {FREE_QUERIES_PER_DAY + NEW_USER_BONUS}")
    
    # Test 3: User balance
    print(f"\n📊 Test 3: User Balance for {user_id}")
    debug_user_balance(user_id)
    
    # Test 4: Force initialization if needed
    balance_info = get_user_balance_info(user_id)
    if balance_info['total_scans'] <= 0:
        print(f"\n📊 Test 4: Force Initialization (user has 0 scans)")
        force_user_initialization(user_id)
        
        # Re-check balance
        balance_info = get_user_balance_info(user_id)
        print(f"✅ After initialization: {balance_info}")
    else:
        print(f"\n📊 Test 4: User Already Has Scans")
        print(f"✅ Current balance: {balance_info}")
    
    # Test 5: Spending simulation
    print(f"\n📊 Test 5: Spending Simulation")
    try:
        allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
        print(f"✅ Rate limit check: allowed={allowed}, reason={reason}")
        
        if allowed:
            print("  Simulating token spend...")
            success, message = spend_fcb_token(user_id, "Debug test")
            print(f"  Spend result: {success} - {message}")
            
            # Check balance after spend
            new_balance = get_user_balance_info(user_id)
            print(f"  Balance after spend: {new_balance}")
        
    except Exception as e:
        print(f"❌ Spending simulation failed: {e}")
    
    print("\n🔧" + "="*50)
    print("🔧 DEBUG TEST COMPLETE")
    print("🔧" + "="*50)

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_token_economics():
    """Initialize the token economics system"""
    logging.info("💰 FCB v2 Token Economics System initialized")
    logging.info(f"📊 Daily free scans: {FREE_QUERIES_PER_DAY}")
    logging.info(f"🎁 New user bonus: {NEW_USER_BONUS}")
    logging.info(f"⏱️ Rate limit: {RATE_LIMIT_WINDOW}s between requests")
    logging.info(f"🎫 Token packages: {len(FCB_STAR_PACKAGES)} available")
    logging.info("🔧 Debug functions available: debug_user_balance(), test_user_balance(), ensure_user_has_scans()")

# Auto-initialize when module is imported
initialize_token_economics()