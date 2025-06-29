"""
Database module for CFB (Crypto FOMO Bot)
Handles user management, FCB tokens, and rate limiting - PostgreSQL Version
OPTIMIZED FOR RENDER DEPLOYMENT WITH PERSISTENCE TESTING
"""

import logging
import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
import time
from contextlib import contextmanager
import threading

# FCB Token Configuration
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# Rate limiting storage
user_last_request = {}

# Global connection pool - initialize once, reuse many times
_connection_pool = None
_pool_lock = threading.Lock()

def initialize_connection_pool():
    """Initialize the connection pool once at startup"""
    global _connection_pool
    
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:  # Double-check locking
                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    raise Exception("DATABASE_URL environment variable not set")
                
                # Parse connection parameters from DATABASE_URL
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(database_url)
                
                try:
                    # Create connection pool with optimal settings
                    _connection_pool = psycopg2.pool.SimpleConnectionPool(
                        minconn=2,      # Minimum connections (always ready)
                        maxconn=10,     # Maximum connections (scale with load)
                        host=parsed.hostname,
                        port=parsed.port,
                        user=parsed.username,
                        password=parsed.password,
                        database=parsed.path[1:],  # Remove leading '/'
                        sslmode='require'
                    )
                    
                    logging.info("🚀 Connection pool created successfully: 2-10 connections")
                    
                    # Test the pool with autocommit
                    test_connection = _connection_pool.getconn()
                    test_connection.autocommit = True  # Enable autocommit for reliability
                    _connection_pool.putconn(test_connection)
                    
                    logging.info("✅ Connection pool tested successfully with autocommit")
                    
                except Exception as e:
                    logging.error(f"❌ Failed to create connection pool: {e}")
                    raise

@contextmanager
def get_db_connection():
    """OPTIMIZED: Get pooled connection with autocommit for speed + reliability"""
    global _connection_pool
    
    # Initialize pool if needed (thread-safe)
    if _connection_pool is None:
        initialize_connection_pool()
    
    conn = None
    try:
        # Get connection from pool (FAST - no new process creation)
        conn = _connection_pool.getconn()
        
        if conn is None:
            raise Exception("No connections available in pool")
        
        # Enable autocommit for immediate persistence (RELIABLE)
        conn.autocommit = True
        
        yield conn
        
    except Exception as e:
        if conn:
            # Return potentially corrupted connection to pool for cleanup
            try:
                _connection_pool.putconn(conn)
            except:
                pass  # Pool will handle cleanup
        logging.error(f"❌ Database connection error: {e}")
        raise
    finally:
        if conn:
            # Return connection to pool for reuse (FAST future operations)
            try:
                _connection_pool.putconn(conn)
            except Exception as e:
                logging.error(f"❌ Error returning connection to pool: {e}")

def close_connection_pool():
    """Close all connections in the pool (call on shutdown)"""
    global _connection_pool
    
    if _connection_pool:
        try:
            _connection_pool.closeall()
            logging.info("🔒 Connection pool closed successfully")
        except Exception as e:
            logging.error(f"❌ Error closing connection pool: {e}")
        finally:
            _connection_pool = None

def init_user_db():
    """Initialize user database with PostgreSQL"""
    try:
        logging.info("🔍 Initializing PostgreSQL database with connection pool...")
        
        # Initialize the connection pool first
        initialize_connection_pool()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create table with PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    fcb_balance INTEGER DEFAULT 0,
                    total_queries INTEGER DEFAULT 0,
                    free_queries_used INTEGER DEFAULT 0,
                    new_user_bonus_used INTEGER DEFAULT 0,
                    has_received_bonus BOOLEAN DEFAULT FALSE,
                    last_free_reset DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_purchase_date TIMESTAMP NULL
                )
            ''')
            
            # Add indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_reset ON users(last_free_reset)
            ''')
            
            # CRITICAL: Explicit commit for table creation
            conn.commit()
            
            # Log database info for debugging
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            logging.info(f"✅ PostgreSQL database initialized successfully")
            logging.info(f"📊 Current user count: {user_count}")
            
            # Test persistence immediately after initialization
            test_token_persistence()
            
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
        raise

def get_user_balance(user_id):
    """Get user's FCB token balance and available queries"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Reset free queries daily
            cursor.execute('''
                UPDATE users 
                SET free_queries_used = 0, last_free_reset = CURRENT_DATE 
                WHERE user_id = %s AND last_free_reset < CURRENT_DATE
            ''', (user_id,))
            
            # Create new user with bonus (PostgreSQL syntax)
            cursor.execute('''
                INSERT INTO users (user_id, has_received_bonus) 
                VALUES (%s, FALSE) 
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id,))
            
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus 
                FROM users WHERE user_id = %s
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            # CRITICAL: Commit all changes
            conn.commit()
            
            if result:
                fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus = result
                
                # Calculate available queries
                daily_remaining = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
                bonus_remaining = max(0, NEW_USER_BONUS - new_user_bonus_used) if not has_received_bonus else 0
                total_free_remaining = daily_remaining + bonus_remaining
                
                return fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus
            
            return 0, 0, 0, NEW_USER_BONUS, False
            
    except Exception as e:
        logging.error(f"Database error in get_user_balance: {e}")
        return 0, 0, 0, 0, False

def spend_fcb_token(user_id):
    """Optimized spending with FOMO language - FIXED VERSION WITH ENHANCED LOGGING"""
    try:
        # Get fresh balance data in the same transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get current user state in a single transaction
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus 
                FROM users WHERE user_id = %s
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                # Create user if doesn't exist
                cursor.execute('''
                    INSERT INTO users (user_id, has_received_bonus) 
                    VALUES (%s, FALSE) 
                    ON CONFLICT (user_id) DO NOTHING
                ''', (user_id,))
                fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus = 0, 0, 0, False
            else:
                fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus = result
            
            # 🔧 ENHANCED LOGGING - Show what we're working with
            logging.info(f"💎 SPEND DEBUG for user {user_id}: FCB={fcb_balance}, Free={free_queries_used}/{FREE_QUERIES_PER_DAY}, Bonus={new_user_bonus_used}/{NEW_USER_BONUS}, HasBonus={has_received_bonus}")
            
            # Priority 1: Use new user bonus first (creates instant engagement)
            if not has_received_bonus and new_user_bonus_used < NEW_USER_BONUS:
                logging.info(f"💎 SPEND PATH: Using bonus scan (Path 1)")
                
                cursor.execute('''
                    UPDATE users 
                    SET new_user_bonus_used = new_user_bonus_used + 1, 
                        total_queries = total_queries + 1,
                        has_received_bonus = CASE 
                            WHEN new_user_bonus_used + 1 >= %s THEN TRUE 
                            ELSE FALSE 
                        END
                    WHERE user_id = %s
                ''', (NEW_USER_BONUS, user_id))
                
                # 🔧 ENHANCED LOGGING - Check what actually happened
                rows_affected = cursor.rowcount
                logging.info(f"💎 Bonus scan UPDATE affected {rows_affected} rows")
                
                # CRITICAL: Commit transaction BEFORE returning
                conn.commit()
                logging.info(f"💎 Bonus token spent by user {user_id}")
                
                remaining_bonus = NEW_USER_BONUS - (new_user_bonus_used + 1)
                daily_remaining = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
                
                if remaining_bonus > 0:
                    return True, f"✨ Welcome scan used! {remaining_bonus} bonus + {daily_remaining} daily scans left."
                else:
                    return True, f"🎁 Last bonus scan used! {daily_remaining} daily scans remaining."
            
            # Priority 2: Use daily free scans
            elif free_queries_used < FREE_QUERIES_PER_DAY:
                logging.info(f"💎 SPEND PATH: Using daily free scan (Path 2)")
                
                cursor.execute('''
                    UPDATE users 
                    SET free_queries_used = free_queries_used + 1, total_queries = total_queries + 1
                    WHERE user_id = %s
                ''', (user_id,))
                
                # 🔧 ENHANCED LOGGING - Check what actually happened
                rows_affected = cursor.rowcount
                logging.info(f"💎 Free scan UPDATE affected {rows_affected} rows")
                
                # CRITICAL: Commit transaction BEFORE returning
                conn.commit()
                logging.info(f"💎 Free token spent by user {user_id}")
                
                remaining_free = FREE_QUERIES_PER_DAY - (free_queries_used + 1)
                if remaining_free > 0:
                    return True, f"🎯 FOMO scan used. {remaining_free} scans remaining today."
                else:
                    return True, "🚨 LAST free scan used! Get unlimited with FCB tokens."
            
            # Priority 3: Use FCB tokens
            elif fcb_balance > 0:
                logging.info(f"💎 SPEND PATH: Using FCB token (Path 3) - Current balance: {fcb_balance}")
                
                cursor.execute('''
                    UPDATE users 
                    SET fcb_balance = fcb_balance - 1, total_queries = total_queries + 1
                    WHERE user_id = %s
                ''', (user_id,))
                
                # 🔧 ENHANCED LOGGING - Check what actually happened
                rows_affected = cursor.rowcount
                logging.info(f"💎 FCB token UPDATE affected {rows_affected} rows")
                
                # 🔧 VERIFY the balance actually changed
                cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
                new_balance = cursor.fetchone()[0]
                logging.info(f"💎 FCB balance after UPDATE: {new_balance} (was {fcb_balance})")
                
                # CRITICAL: Commit transaction BEFORE returning
                conn.commit()
                logging.info(f"💎 Paid token spent by user {user_id} (balance was {fcb_balance}, now {new_balance})")
                
                return True, f"💎 1 FCB token spent. Balance: {new_balance} tokens"
            
            # No scans available - CONVERSION OPPORTUNITY!
            else:
                logging.info(f"💎 SPEND PATH: No tokens available (Path 4)")
                return False, "💔 No FOMO scans remaining! Time to go premium with FCB tokens."
                
    except Exception as e:
        logging.error(f"❌ Database error in spend_fcb_token for user {user_id}: {e}")
        return False, "❌ Database error. Please try again."

def add_fcb_tokens(user_id, amount):
    """Add FCB tokens to user's balance with enhanced persistence verification"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure user exists (PostgreSQL syntax)
            cursor.execute('''
                INSERT INTO users (user_id) 
                VALUES (%s) 
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id,))
            
            # Get current balance for logging
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            old_balance = result[0] if result else 0
            
            # Add tokens
            cursor.execute('''
                UPDATE users SET fcb_balance = fcb_balance + %s, first_purchase_date = COALESCE(first_purchase_date, CURRENT_TIMESTAMP) 
                WHERE user_id = %s
            ''', (amount, user_id))

            # Verify the update worked BEFORE committing
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            new_balance = result[0] if result else 0
            
            # CRITICAL: Commit transaction
            conn.commit()
            
            # VERIFICATION: Read balance again after commit to ensure persistence
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            verified_balance = result[0] if result else 0
            
            logging.info(f"✅ FCB tokens added: User {user_id}, {old_balance} → {new_balance} → {verified_balance} (+{amount})")
            
            if verified_balance != new_balance:
                logging.error(f"❌ PERSISTENCE ERROR: Expected {new_balance}, got {verified_balance}")
                return False, 0
            
            return True, new_balance
            
    except Exception as e:
        logging.error(f"❌ Database error in add_fcb_tokens: {e}")
        return False, 0

def check_rate_limit_with_fcb(user_id, rate_limit_seconds=1):
    """Optimized rate limiting - reduced to 1 second"""
    current_time = time.time()
    
    # Check if user has queries available
    fcb_balance, _, _, total_free_remaining, _ = get_user_balance(user_id)
    has_queries = total_free_remaining > 0 or fcb_balance > 0
    
    if not has_queries:
        return False, 0, "No queries available"
    
    # Very short rate limit - let them burn through queries!
    if user_id not in user_last_request:
        user_last_request[user_id] = current_time
        return True, 0, "First request"
    
    time_since_last = current_time - user_last_request[user_id]
    
    if time_since_last >= rate_limit_seconds:
        user_last_request[user_id] = current_time
        return True, 0, "Rate limit passed"
    else:
        time_remaining = rate_limit_seconds - time_since_last
        return False, int(time_remaining), "Rate limited"
    
def get_user_balance_detailed(user_id):
    """Get detailed user balance for debugging"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Reset free queries daily
            cursor.execute('''
                UPDATE users 
                SET free_queries_used = 0, last_free_reset = CURRENT_DATE 
                WHERE user_id = %s AND last_free_reset < CURRENT_DATE
            ''', (user_id,))
            
            # Create new user with bonus (PostgreSQL syntax)
            cursor.execute('''
                INSERT INTO users (user_id, has_received_bonus) 
                VALUES (%s, FALSE) 
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id,))
            
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, 
                       has_received_bonus, total_queries, created_at, first_purchase_date
                FROM users WHERE user_id = %s
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            # CRITICAL: Commit changes
            conn.commit()
            
            if result:
                fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus, total_queries, created_at, first_purchase_date = result
                
                # Calculate available queries
                daily_remaining = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
                bonus_remaining = max(0, NEW_USER_BONUS - new_user_bonus_used) if not has_received_bonus else 0
                total_free_remaining = daily_remaining + bonus_remaining
                
                return {
                    'fcb_balance': fcb_balance,
                    'free_queries_used': free_queries_used,
                    'new_user_bonus_used': new_user_bonus_used,
                    'total_free_remaining': total_free_remaining,
                    'has_received_bonus': has_received_bonus,
                    'total_queries': total_queries,
                    'created_at': created_at,
                    'first_purchase_date': first_purchase_date
                }
            
            return None
            
    except Exception as e:
        logging.error(f"Database error in get_user_balance_detailed: {e}")
        return None

def verify_database_integrity():
    """Debug function to verify database state and persistence"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE fcb_balance > 0")
            users_with_tokens = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(fcb_balance), 0) FROM users")
            total_tokens = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE first_purchase_date IS NOT NULL")
            paid_users = cursor.fetchone()[0]
            
            logging.info(f"🔍 Database stats: {total_users} users, {users_with_tokens} with tokens, {total_tokens} total tokens")
            
            return {
                'total_users': total_users,
                'users_with_tokens': users_with_tokens,
                'total_tokens': total_tokens,
                'paid_users': paid_users,
                'persistence_status': 'WORKING' if users_with_tokens > 0 else 'NO_TOKENS_YET'
            }
            
    except Exception as e:
        logging.error(f"Database integrity check failed: {e}")
        return None

def test_token_persistence():
    """AGGRESSIVE: Test function that FORCES FCB token usage by completely resetting user state"""
    try:
        test_user_id = 999999  # Use a unique test user ID
        test_amount = 100
        
        logging.info("🧪 === STARTING AGGRESSIVE TOKEN PERSISTENCE TEST ===")
        
        # Step 1: AGGRESSIVE user reset - completely delete and recreate
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Complete deletion
            cursor.execute('DELETE FROM users WHERE user_id = %s', (test_user_id,))
            logging.info(f"🧪 Deleted any existing test user {test_user_id}")
            
            # Create user with ZERO everything - force FCB path
            cursor.execute('''
                INSERT INTO users (
                    user_id, 
                    fcb_balance, 
                    has_received_bonus, 
                    new_user_bonus_used, 
                    free_queries_used, 
                    last_free_reset,
                    total_queries
                ) VALUES (%s, 0, TRUE, %s, %s, CURRENT_DATE, 0)
            ''', (test_user_id, NEW_USER_BONUS, FREE_QUERIES_PER_DAY))
            
            # Verify the user state
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus, last_free_reset
                FROM users WHERE user_id = %s
            ''', (test_user_id,))
            
            result = cursor.fetchone()
            if result:
                fcb, free_used, bonus_used, has_bonus, last_reset = result
                logging.info(f"🧪 Test user created: FCB={fcb}, Free={free_used}/{FREE_QUERIES_PER_DAY}, Bonus={bonus_used}/{NEW_USER_BONUS}, HasBonus={has_bonus}")
            else:
                logging.error("❌ Failed to create test user")
                return False
        
        # Step 2: Add FCB tokens
        logging.info(f"💰 Adding {test_amount} FCB tokens to test user...")
        success, new_balance = add_fcb_tokens(test_user_id, test_amount)
        logging.info(f"💰 Add tokens result: success={success}, new_balance={new_balance}")
        
        if not success or new_balance != test_amount:
            logging.error("❌ CRITICAL: Failed to add tokens to test user")
            return False
        
        # Step 3: Double-check user state before spending
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus,
                       (free_queries_used < %s) as has_free_scans,
                       (NOT has_received_bonus AND new_user_bonus_used < %s) as has_bonus_scans
                FROM users WHERE user_id = %s
            ''', (FREE_QUERIES_PER_DAY, NEW_USER_BONUS, test_user_id))
            
            result = cursor.fetchone()
            if result:
                fcb, free_used, bonus_used, has_bonus, has_free, has_bonus_scans = result
                logging.info(f"🔍 Pre-spend state: FCB={fcb}, Free={free_used}/{FREE_QUERIES_PER_DAY}, Bonus={bonus_used}/{NEW_USER_BONUS}")
                logging.info(f"🔍 Available scans: Free={has_free}, Bonus={has_bonus_scans}, Should use FCB={not has_free and not has_bonus_scans}")
                
                if has_free or has_bonus_scans:
                    logging.error(f"❌ TEST SETUP FAILED: User still has free scans available!")
                    logging.error(f"❌ This will cause spend_fcb_token() to use wrong path")
                    return False
        
        logging.info("✅ Test user properly configured - NO free scans available")
        
        # Step 4: FORCE FCB TOKEN SPENDING
        logging.info("🧪 === TESTING FORCED FCB TOKEN SPENDING ===")
        
        # Check balance before spending
        pre_spend_balance = get_user_balance(test_user_id)[0]
        logging.info(f"💎 Balance before spending: {pre_spend_balance}")
        
        # Attempt to spend token
        logging.info("💎 Calling spend_fcb_token() - MUST use Path 3 (FCB tokens)...")
        spend_success, spend_message = spend_fcb_token(test_user_id)
        logging.info(f"💎 spend_fcb_token() returned: success={spend_success}, message='{spend_message}'")
        
        if spend_success:
            # Check balance immediately after spending
            post_spend_balance = get_user_balance(test_user_id)[0]
            logging.info(f"💎 Balance after spending: {post_spend_balance}")
            
            # Expected vs actual
            expected_balance = pre_spend_balance - 1
            logging.info(f"💎 Expected: {expected_balance}, Actual: {post_spend_balance}")
            
            if post_spend_balance == expected_balance:
                logging.info("✅ ✅ ✅ FCB TOKEN SPENDING WORKS PERFECTLY ✅ ✅ ✅")
                
                # Step 5: Test persistence
                logging.info("🔄 Testing persistence...")
                restart_balance = get_user_balance(test_user_id)[0]
                
                if restart_balance == expected_balance:
                    logging.info("✅ ✅ ✅ TOKENS PERSIST CORRECTLY ✅ ✅ ✅")
                    logging.info("🎉 🎉 🎉 ALL TESTS PASSED - SYSTEM WORKING 🎉 🎉 🎉")
                    cleanup_test_user()
                    return True
                else:
                    logging.error(f"❌ PERSISTENCE ERROR: Expected {expected_balance}, got {restart_balance}")
            else:
                logging.error(f"❌ FCB SPENDING ERROR: Expected {expected_balance}, got {post_spend_balance}")
                logging.error("❌ This indicates the wrong spending path was used!")
        else:
            logging.error(f"❌ FCB TOKEN SPENDING FAILED: {spend_message}")
        
        # Clean up on failure
        cleanup_test_user()
        return False
            
    except Exception as e:
        logging.error(f"❌ AGGRESSIVE PERSISTENCE TEST FAILED: {e}")
        import traceback
        logging.error(f"❌ Full traceback: {traceback.format_exc()}")
        cleanup_test_user()
        return False

def simple_spend_test(user_id):
    """SIMPLE test to spend exactly 1 token with minimal logic"""
    try:
        logging.info(f"🧪 === SIMPLE SPEND TEST for user {user_id} ===")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Step 1: Check current balance
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            if not result:
                logging.error("❌ User not found for simple spend test")
                return False
                
            current_balance = result[0]
            logging.info(f"💰 Current balance in simple test: {current_balance}")
            
            if current_balance <= 0:
                logging.error("❌ No tokens to spend in simple test")
                return False
            
            # Step 2: Subtract 1 token
            cursor.execute('''
                UPDATE users 
                SET fcb_balance = fcb_balance - 1, total_queries = total_queries + 1
                WHERE user_id = %s
            ''', (user_id,))
            
            # Step 3: Check rows affected
            rows_affected = cursor.rowcount
            logging.info(f"💰 Rows affected by UPDATE: {rows_affected}")
            
            # With autocommit=True, no need to manually commit
            logging.info("💰 Transaction auto-committed")
            
            # Step 4: Verify immediately in same connection
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            new_balance = result[0] if result else None
            logging.info(f"💰 Balance after update (same connection): {new_balance}")
            
            expected_balance = current_balance - 1
            if new_balance == expected_balance:
                logging.info("✅ SIMPLE SPEND TEST PASSED")
                return True
            else:
                logging.error(f"❌ SIMPLE SPEND TEST FAILED: Expected {expected_balance}, got {new_balance}")
                return False
                
    except Exception as e:
        logging.error(f"❌ Simple spend test failed: {e}")
        return False

def cleanup_test_user():
    """Clean up test user after testing"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = 999999")
            # With autocommit=True, no need to manually commit
            logging.info("🧹 Test user cleaned up")
    except Exception as e:
        logging.error(f"❌ Test cleanup failed: {e}")

def test_performance_improvement():
    """Test the performance improvement of connection pooling"""
    import time
    
    logging.info("🧪 Testing connection pool performance...")
    
    # Test connection pool speed
    start_time = time.time()
    for i in range(10):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
    pool_time = time.time() - start_time
    
    logging.info(f"⚡ Connection pool: 10 operations in {pool_time:.3f}s ({pool_time/10*1000:.1f}ms per operation)")
    
    # Performance target achieved if under 500ms per operation
    avg_time_ms = (pool_time / 10) * 1000
    if avg_time_ms < 500:
        logging.info(f"✅ PERFORMANCE TARGET ACHIEVED: {avg_time_ms:.1f}ms < 500ms")
    else:
        logging.warning(f"⚠️ Performance target missed: {avg_time_ms:.1f}ms > 500ms")
    
    return avg_time_ms