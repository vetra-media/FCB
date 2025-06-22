"""
Database module for CFB (Crypto FOMO Bot)
Handles user management, FCB tokens, and rate limiting
"""

import sqlite3
import time
import logging
import os
from contextlib import contextmanager

# FCB Token Configuration
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# Rate limiting storage
user_last_request = {}

# ✅ RENDER-FIXED: Safe database path handling
DATABASE_PATH = os.getenv('DATABASE_PATH', 'fcb_users.db')

# ✅ RENDER-SAFE: Only create directory if path actually has a directory
db_dir = os.path.dirname(DATABASE_PATH)
if db_dir and db_dir != '':  # This prevents the empty string error
    try:
        os.makedirs(db_dir, exist_ok=True)
        logging.info(f"✅ Database directory created: {db_dir}")
    except Exception as e:
        logging.warning(f"Could not create database directory: {e}")

logging.info(f"🔍 Database path: {DATABASE_PATH}")

@contextmanager
def get_db_connection():
    """Simple, reliable context manager"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    try:
        yield conn
    finally:
        conn.close()

def init_user_db():
    """Initialize user database with enhanced error handling"""
    try:
        # ✅ Log the database path for debugging
        logging.info(f"🔍 Initializing database at: {DATABASE_PATH}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create table with proper error handling
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
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
            
            # ✅ ADD THIS: Explicit commit
            conn.commit()
            
            # ✅ Log database info for debugging
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            logging.info(f"✅ Database initialized successfully at {DATABASE_PATH}")
            logging.info(f"📊 Current user count: {user_count}")
            
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
        logging.error(f"❌ Database path: {DATABASE_PATH}")
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
                WHERE user_id = ? AND last_free_reset < CURRENT_DATE
            ''', (user_id,))
            
            # Create new user with bonus
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, has_received_bonus) VALUES (?, FALSE)
            ''', (user_id,))
            
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, has_received_bonus 
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
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
    """Optimized spending with FOMO language"""
    try:
        fcb_balance, free_queries_used, new_user_bonus_used, total_free_remaining, has_received_bonus = get_user_balance(user_id)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Priority 1: Use new user bonus first (creates instant engagement)
            if not has_received_bonus and new_user_bonus_used < NEW_USER_BONUS:
                cursor.execute('''
                    UPDATE users 
                    SET new_user_bonus_used = new_user_bonus_used + 1, 
                        total_queries = total_queries + 1,
                        has_received_bonus = CASE 
                            WHEN new_user_bonus_used + 1 >= ? THEN TRUE 
                            ELSE FALSE 
                        END
                    WHERE user_id = ?
                ''', (NEW_USER_BONUS, user_id))
                conn.commit()
                
                remaining_bonus = NEW_USER_BONUS - (new_user_bonus_used + 1)
                daily_remaining = max(0, FREE_QUERIES_PER_DAY - free_queries_used)
                
                if remaining_bonus > 0:
                    return True, f"✨ Welcome scan used! {remaining_bonus} bonus + {daily_remaining} daily scans left."
                else:
                    return True, f"🎁 Last bonus scan used! {daily_remaining} daily scans remaining."
            
            # Priority 2: Use daily free scans
            elif free_queries_used < FREE_QUERIES_PER_DAY:
                cursor.execute('''
                    UPDATE users 
                    SET free_queries_used = free_queries_used + 1, total_queries = total_queries + 1
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                
                remaining_free = FREE_QUERIES_PER_DAY - (free_queries_used + 1)
                if remaining_free > 0:
                    return True, f"🎯 FOMO scan used. {remaining_free} scans remaining today."
                else:
                    return True, "🚨 LAST free scan used! Get unlimited with FCB tokens."
            
            # Priority 3: Use FCB tokens
            elif fcb_balance > 0:
                cursor.execute('''
                    UPDATE users 
                    SET fcb_balance = fcb_balance - 1, total_queries = total_queries + 1
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return True, f"💎 1 FCB token spent. Balance: {fcb_balance - 1} tokens"
            
            # No scans available - CONVERSION OPPORTUNITY!
            else:
                return False, "💔 No FOMO scans remaining! Time to go premium with FCB tokens."
                
    except Exception as e:
        logging.error(f"Database error in spend_fcb_token: {e}")
        return False, "❌ Database error. Please try again."

def add_fcb_tokens(user_id, amount):
    """Add FCB tokens to user's balance with better error handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure user exists
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id) VALUES (?)
            ''', (user_id,))
            
            # Get current balance for logging
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            old_balance = result[0] if result else 0
            
            # Add tokens
            cursor.execute('''
                UPDATE users SET fcb_balance = fcb_balance + ? WHERE user_id = ?
            ''', (amount, user_id))

            # Verify the update worked
            cursor.execute('SELECT fcb_balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            new_balance = result[0] if result else 0
            
            conn.commit()
            
            logging.info(f"✅ FCB tokens added: User {user_id}, {old_balance} → {new_balance} (+{amount})")
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
                WHERE user_id = ? AND last_free_reset < CURRENT_DATE
            ''', (user_id,))
            
            # Create new user with bonus
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, has_received_bonus) VALUES (?, FALSE)
            ''', (user_id,))
            
            cursor.execute('''
                SELECT fcb_balance, free_queries_used, new_user_bonus_used, 
                       has_received_bonus, total_queries, created_at, first_purchase_date
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
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

# ✅ Add database backup functionality
def backup_database():
    """Create a backup of the database"""
    try:
        import shutil
        backup_path = f"{DATABASE_PATH}.backup"
        shutil.copy2(DATABASE_PATH, backup_path)
        logging.info(f"✅ Database backed up to {backup_path}")
        return True
    except Exception as e:
        logging.error(f"❌ Database backup failed: {e}")
        return False
    
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
            
            cursor.execute("SELECT SUM(fcb_balance) FROM users")
            total_tokens = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE first_purchase_date IS NOT NULL")
            paid_users = cursor.fetchone()[0]
            
            # Check file integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            logging.info(f"🔍 Database stats: {total_users} users, {users_with_tokens} with tokens, {total_tokens} total tokens")
            
            return {
                'total_users': total_users,
                'users_with_tokens': users_with_tokens,
                'total_tokens': total_tokens,
                'paid_users': paid_users,
                'integrity_check': integrity_result,
                'persistence_status': 'WORKING' if users_with_tokens > 0 else 'NO_TOKENS_YET'
            }
            
    except Exception as e:
        logging.error(f"Database integrity check failed: {e}")
        return None