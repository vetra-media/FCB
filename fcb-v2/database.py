"""
Database module for CFB (Crypto FOMO Bot)
Handles user management, FCB tokens, rate limiting, AND subscription management
"""

import sqlite3
import time
import logging
import os
import re
import pickle
from contextlib import contextmanager
from datetime import datetime

# FCB Token Configuration
FREE_QUERIES_PER_DAY = 5
NEW_USER_BONUS = 3

# Rate limiting storage
user_last_request = {}

# ✅ FIXED: Use environment variable for database path with fallback
DATABASE_PATH = os.getenv('DATABASE_PATH', '/tmp/fcb_users.db')

# ✅ Ensure database directory exists
try:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
except Exception as e:
    # If we can't create the directory, fall back to current directory
    logging.warning(f"Could not create database directory, using current directory: {e}")
    DATABASE_PATH = 'fcb_users.db'

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        # ✅ FIXED: Use persistent path instead of relative path
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        yield conn
    finally:
        if conn:
            conn.close()

# ===============================================
# ✅ SUBSCRIPTION MANAGEMENT FUNCTIONS
# ===============================================

def add_user_to_notifications(user_id):
    """Add user to notification subscription list"""
    try:
        # Load existing subscriptions
        subscriptions_file = 'subscriptions.pkl'
        
        if os.path.exists(subscriptions_file):
            with open(subscriptions_file, 'rb') as f:
                subscribed_users = pickle.load(f)
        else:
            subscribed_users = set()
        
        # Add user to set (automatically handles duplicates)
        subscribed_users.add(user_id)
        
        # Save updated subscriptions
        with open(subscriptions_file, 'wb') as f:
            pickle.dump(subscribed_users, f)
        
        logging.info(f"✅ User {user_id} added to notifications")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error adding user to notifications: {e}")
        return False

def get_subscribed_users():
    """Get list of all subscribed users"""
    try:
        subscriptions_file = 'subscriptions.pkl'
        
        if os.path.exists(subscriptions_file):
            with open(subscriptions_file, 'rb') as f:
                subscribed_users = pickle.load(f)
                
            # Convert to list for compatibility
            return list(subscribed_users)
        else:
            logging.warning("⚠️  No subscriptions.pkl file found")
            return []
            
    except Exception as e:
        logging.error(f"❌ Error getting subscribed users: {e}")
        return []

def remove_user_from_notifications(user_id):
    """Remove user from notification subscription list"""
    try:
        subscriptions_file = 'subscriptions.pkl'
        
        if os.path.exists(subscriptions_file):
            with open(subscriptions_file, 'rb') as f:
                subscribed_users = pickle.load(f)
            
            # Remove user if they exist
            subscribed_users.discard(user_id)
            
            # Save updated subscriptions
            with open(subscriptions_file, 'wb') as f:
                pickle.dump(subscribed_users, f)
            
            logging.info(f"✅ User {user_id} removed from notifications")
            return True
        else:
            return False
            
    except Exception as e:
        logging.error(f"❌ Error removing user from notifications: {e}")
        return False

def get_subscription_count():
    """Get total number of subscribed users"""
    try:
        subscribed_users = get_subscribed_users()
        return len(subscribed_users)
    except Exception as e:
        logging.error(f"❌ Error getting subscription count: {e}")
        return 0

# ===============================================
# ✅ CAMPAIGN TRACKING FUNCTIONS
# ===============================================

def init_campaign_tracking():
    """Add campaign tracking columns if they don't exist"""
    # Import here to avoid circular imports
    try:
        from config import CAMPAIGN_TRACKING_ENABLED, MIN_USERS_FOR_STATS
    except ImportError:
        CAMPAIGN_TRACKING_ENABLED = True  # Default fallback
        MIN_USERS_FOR_STATS = 5
        
    if not CAMPAIGN_TRACKING_ENABLED:
        return
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Add campaign columns to existing users table
            columns_to_add = [
                "campaign_source TEXT DEFAULT NULL",
                "campaign_medium TEXT DEFAULT NULL", 
                "referral_code TEXT DEFAULT NULL",
                "acquisition_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "first_interaction_type TEXT DEFAULT 'organic'"
            ]
            
            for column in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column}")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
            
            conn.commit()
            logging.info("✅ Campaign tracking columns initialized")
            
    except Exception as e:
        logging.error(f"❌ Campaign tracking init error: {e}")

def track_user_campaign(user_id: int, campaign_code: str = None):
    """Track user acquisition source (integrated with existing user system)"""
    # Import here to avoid circular imports
    try:
        from config import CAMPAIGN_TRACKING_ENABLED
    except ImportError:
        CAMPAIGN_TRACKING_ENABLED = True  # Default fallback
        
    if not CAMPAIGN_TRACKING_ENABLED:
        return 'organic'
        
    try:
        # Parse campaign code
        if campaign_code:
            campaign_code = re.sub(r'[^a-zA-Z0-9_-]', '', campaign_code)[:64]
            parts = campaign_code.split('_')
            source = parts[0] if parts else 'unknown'
            medium = parts[1] if len(parts) > 1 else 'direct'
            referral = '_'.join(parts[2:]) if len(parts) > 2 else campaign_code
            interaction_type = 'campaign'
        else:
            source = 'organic'
            medium = 'direct'
            referral = None
            interaction_type = 'organic'
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists and has campaign data
            cursor.execute("SELECT campaign_source FROM users WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing and existing[0]:
                # Don't override existing campaign data
                return existing[0]
            
            # Update or insert with campaign data
            if existing:
                cursor.execute("""
                    UPDATE users 
                    SET campaign_source = ?, campaign_medium = ?, 
                        referral_code = ?, first_interaction_type = ?
                    WHERE user_id = ?
                """, (source, medium, referral, interaction_type, user_id))
            else:
                # This integrates with your existing get_or_create_user logic
                cursor.execute("""
                    INSERT OR IGNORE INTO users 
                    (user_id, campaign_source, campaign_medium, referral_code, 
                     first_interaction_type, fcb_balance, total_queries, 
                     free_queries_used, new_user_bonus_used, has_received_bonus)
                    VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, FALSE)
                """, (user_id, source, medium, referral, interaction_type))
            
            conn.commit()
            logging.info(f"📈 User {user_id} tracked: {source} (code: {campaign_code})")
            return source
            
    except Exception as e:
        logging.error(f"❌ Campaign tracking error: {e}")
        return 'error'

def get_campaign_analytics():
    """Get campaign performance data"""
    # Import here to avoid circular imports
    try:
        from config import CAMPAIGN_TRACKING_ENABLED, MIN_USERS_FOR_STATS
    except ImportError:
        CAMPAIGN_TRACKING_ENABLED = True
        MIN_USERS_FOR_STATS = 5
        
    if not CAMPAIGN_TRACKING_ENABLED:
        return {}
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Users by source
            cursor.execute("""
                SELECT campaign_source, COUNT(*) as users
                FROM users 
                WHERE campaign_source IS NOT NULL
                GROUP BY campaign_source
                ORDER BY users DESC
            """)
            by_source = dict(cursor.fetchall())
            
            # Conversion rates (users who made purchases)
            cursor.execute("""
                SELECT campaign_source, 
                       COUNT(*) as total,
                       COUNT(first_purchase_date) as buyers,
                       ROUND(CAST(COUNT(first_purchase_date) AS FLOAT) / COUNT(*) * 100, 2) as rate
                FROM users 
                WHERE campaign_source IS NOT NULL
                GROUP BY campaign_source
                HAVING COUNT(*) >= ?
                ORDER BY rate DESC
            """, (MIN_USERS_FOR_STATS,))
            conversion_data = cursor.fetchall()
            
            return {
                'sources': by_source,
                'conversions': conversion_data
            }
            
    except Exception as e:
        logging.error(f"❌ Analytics error: {e}")
        return {}

# ===============================================
# ✅ USER DATABASE FUNCTIONS
# ===============================================

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
    
    # Initialize campaign tracking after main database
    init_campaign_tracking()

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