"""
FCB v2 Session Management System
Complete recreation of FCB v1's sophisticated session management
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# =============================================================================
# CORE SESSION MANAGEMENT
# =============================================================================

# Global session storage - {user_id: session_data}
user_sessions: Dict[int, Dict[str, Any]] = {}

def get_user_session(user_id: int) -> Dict[str, Any]:
    """
    Get or create user-specific session for navigation history with cached data
    Auto-cleans old sessions to prevent memory leaks
    """
    current_time = time.time()
    
    # Clean old sessions (older than 24 hours) to prevent memory leaks
    cleanup_old_sessions(current_time)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'history': [],                    # List of coin IDs in navigation order
            'index': 0,                      # Current position in history
            'last_activity': current_time,   # For session cleanup
            'cached_data': {},               # Cached coin data for FREE navigation
            'from_alert': False,             # Track if session started from alert
            'created_at': current_time       # Session creation timestamp
        }
        logging.info(f"📱 Created new session for user {user_id}")
    else:
        # Update activity timestamp
        user_sessions[user_id]['last_activity'] = current_time
    
    return user_sessions[user_id]

def cleanup_old_sessions(current_time: float):
    """
    Remove sessions older than 24 hours to prevent memory leaks
    Critical for long-running bot stability
    """
    cutoff_time = current_time - (24 * 3600)  # 24 hours ago
    
    old_users = [
        user_id for user_id, session in user_sessions.items()
        if session['last_activity'] < cutoff_time
    ]
    
    for user_id in old_users:
        del user_sessions[user_id]
        logging.info(f"🧹 Cleaned up old session for user {user_id}")

# =============================================================================
# NAVIGATION HISTORY MANAGEMENT
# =============================================================================

def add_to_user_history(user_id: int, coin_id: str, coin_data: Dict = None, from_alert: bool = False) -> Dict[str, Any]:
    """
    Add coin to user's navigation history with cached data for FREE future navigation
    
    Args:
        user_id: Telegram user ID
        coin_id: CoinGecko coin ID
        coin_data: Full coin data to cache (enables FREE navigation)
        from_alert: True if this coin came from an alert (special tracking)
    
    Returns:
        Updated session data
    """
    session = get_user_session(user_id)
    
    # Track if this coin came from an alert (affects navigation behavior)
    if from_alert:
        session['from_alert'] = True
        logging.info(f"🚨 User {user_id}: Starting navigation from alert coin {coin_id}")
    
    # Only add if it's different from the last coin (avoid duplicates)
    if not session['history'] or session['history'][-1] != coin_id:
        session['history'].append(coin_id)
        # Set index to newest coin (user is now viewing this coin)
        session['index'] = len(session['history']) - 1
        
        # Cache the coin data for FREE navigation later
        if coin_data:
            session['cached_data'][coin_id] = {
                'coin_data': coin_data,          # Full coin information
                'cached_at': time.time(),        # Cache timestamp
                'from_alert': from_alert         # Source tracking
            }
            logging.info(f"💾 User {user_id}: Cached data for {coin_id} to enable FREE navigation")
        
        logging.info(f"📝 User {user_id}: Added {coin_id} to history at position {session['index'] + 1}")
    
    return session

def get_cached_coin_data(user_id: int, coin_id: str) -> Optional[Dict]:
    """
    Get cached coin data for FREE navigation
    Returns None if no cache or cache expired (1 hour TTL)
    """
    session = get_user_session(user_id)
    cached_data = session.get('cached_data', {}).get(coin_id)
    
    if cached_data:
        # Check if cache is still fresh (within 1 hour)
        cache_age = time.time() - cached_data.get('cached_at', 0)
        
        if cache_age < 3600:  # 1 hour cache TTL
            logging.info(f"🆓 Using cached data for {coin_id} (age: {cache_age:.0f}s) - FREE navigation")
            return cached_data['coin_data']
        else:
            # Cache expired - remove it
            del session['cached_data'][coin_id]
            logging.info(f"⏰ Cache expired for {coin_id} (age: {cache_age:.0f}s) - would need fresh API call")
            return None
    
    logging.info(f"❌ No cached data for {coin_id} - would need fresh API call")
    return None

def add_alert_coin_to_history(user_id: int, coin_id: str) -> Dict[str, Any]:
    """
    Special function to add alert coins to user history
    Marks session as starting from alert for special navigation behavior
    """
    session = add_to_user_history(user_id, coin_id, from_alert=True)
    logging.info(f"🚨 Alert coin {coin_id} added to user {user_id} history for FREE navigation")
    return session

# =============================================================================
# NAVIGATION STATE HELPERS
# =============================================================================

def get_session_navigation_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed navigation state for a user session
    Used for smart button generation and navigation logic
    """
    if user_id not in user_sessions:
        return None
    
    session = user_sessions[user_id]
    history = session.get('history', [])
    current_index = session.get('index', 0)
    
    # Validate index bounds
    if history and current_index >= len(history):
        current_index = len(history) - 1
        session['index'] = current_index
    
    return {
        'can_go_back': current_index > 0,
        'can_go_forward': current_index < len(history) - 1,
        'current_position': current_index + 1,
        'total_coins': len(history),
        'current_coin': history[current_index] if history and 0 <= current_index < len(history) else None,
        'from_alert_session': session.get('from_alert', False),
        'has_cached_data': session.get('current_coin') in session.get('cached_data', {}) if history else False
    }

def can_navigate_back_free(user_id: int) -> bool:
    """Check if user can navigate back using cached data (FREE)"""
    nav_state = get_session_navigation_state(user_id)
    return nav_state is not None and nav_state['can_go_back']

def can_navigate_forward_free(user_id: int) -> bool:
    """Check if user can navigate forward through existing history (FREE)"""
    nav_state = get_session_navigation_state(user_id)
    return nav_state is not None and nav_state['can_go_forward']

def get_current_coin_id(user_id: int) -> Optional[str]:
    """Get the coin ID user is currently viewing"""
    nav_state = get_session_navigation_state(user_id)
    return nav_state['current_coin'] if nav_state else None

# =============================================================================
# NAVIGATION ACTIONS
# =============================================================================

def navigate_back(user_id: int) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Navigate back in user's history (always FREE)
    
    Returns:
        (success, coin_id, cached_data)
    """
    session = get_user_session(user_id)
    
    if not session.get('history') or session.get('index', 0) <= 0:
        return False, None, None
    
    # Move back one position
    session['index'] -= 1
    target_coin_id = session['history'][session['index']]
    
    # Get cached data if available
    cached_data = get_cached_coin_data(user_id, target_coin_id)
    
    logging.info(f"⬅️ User {user_id}: FREE back navigation to {target_coin_id} (position {session['index'] + 1})")
    
    return True, target_coin_id, cached_data

def navigate_forward(user_id: int) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Navigate forward in user's history (FREE if exists, otherwise needs new discovery)
    
    Returns:
        (success, coin_id, cached_data)
    """
    session = get_user_session(user_id)
    history = session.get('history', [])
    current_index = session.get('index', 0)
    
    # Check if we can move forward through existing history
    if current_index < len(history) - 1:
        # FREE forward navigation through existing history
        session['index'] += 1
        target_coin_id = history[session['index']]
        cached_data = get_cached_coin_data(user_id, target_coin_id)
        
        logging.info(f"➡️ User {user_id}: FREE forward navigation to {target_coin_id} (position {session['index'] + 1})")
        return True, target_coin_id, cached_data
    else:
        # At end of history - would need new discovery (costs token)
        logging.info(f"🔍 User {user_id}: At end of history, new discovery needed (costs 1 token)")
        return False, None, None

# =============================================================================
# SESSION DEBUGGING AND MANAGEMENT
# =============================================================================

def debug_user_session(user_id: int, context: str = ""):
    """Debug function to log user session state"""
    if user_id in user_sessions:
        session = user_sessions[user_id]
        cached_count = len(session.get('cached_data', {}))
        
        logging.info(f"🔍 SESSION DEBUG for User {user_id} ({context}):")
        logging.info(f"  History: {session['history']}")
        logging.info(f"  Index: {session['index']}")
        logging.info(f"  History length: {len(session['history'])}")
        logging.info(f"  Cached coins: {cached_count}")
        logging.info(f"  From alert: {session.get('from_alert', False)}")
        
        if session['history'] and 0 <= session['index'] < len(session['history']):
            current_coin = session['history'][session['index']]
            is_cached = current_coin in session.get('cached_data', {})
            logging.info(f"  Current coin: {current_coin} (cached: {is_cached})")
        else:
            logging.info(f"  ❌ Index out of bounds!")
    else:
        logging.info(f"🔍 SESSION DEBUG: User {user_id} has no session")

def clear_user_session(user_id: int) -> bool:
    """Clear a user's session (for testing or troubleshooting)"""
    if user_id in user_sessions:
        del user_sessions[user_id]
        logging.info(f"🗑️ Cleared session for user {user_id}")
        return True
    return False

def get_session_stats() -> Dict[str, Any]:
    """Get overall session statistics for monitoring"""
    total_sessions = len(user_sessions)
    total_cached_items = sum(len(session.get('cached_data', {})) for session in user_sessions.values())
    active_sessions = sum(1 for session in user_sessions.values() 
                         if time.time() - session['last_activity'] < 3600)  # Active in last hour
    
    return {
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_cached_items': total_cached_items,
        'memory_usage_mb': round(total_cached_items * 0.01, 2)  # Rough estimate
    }

# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def clean_expired_cache():
    """Clean expired cache entries from all sessions"""
    current_time = time.time()
    total_cleaned = 0
    
    for user_id, session in user_sessions.items():
        cached_data = session.get('cached_data', {})
        expired_coins = []
        
        for coin_id, cache_info in cached_data.items():
            cache_age = current_time - cache_info.get('cached_at', 0)
            if cache_age > 3600:  # 1 hour TTL
                expired_coins.append(coin_id)
        
        for coin_id in expired_coins:
            del cached_data[coin_id]
            total_cleaned += 1
    
    if total_cleaned > 0:
        logging.info(f"🧹 Cleaned {total_cleaned} expired cache entries")
    
    return total_cleaned

# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_coingecko_id(coin_id: str) -> bool:
    """
    Validate CoinGecko ID format - CRITICAL for API safety
    Prevents problematic IDs that could crash the system
    """
    if not coin_id or not isinstance(coin_id, str):
        return False
    
    # Remove common invalid patterns that cause issues
    invalid_patterns = [
        'unknown', '', None, 'null', 'undefined',
        'jerry-the-turtle-by-matt-furie',
        'agenda-47'
    ]
    
    if coin_id.lower() in [str(p).lower() for p in invalid_patterns if p]:
        logging.warning(f"🔧 VALIDATION: Rejected known problematic ID: {coin_id}")
        return False
    
    # Basic format validation
    if len(coin_id) < 2 or len(coin_id) > 100:
        return False
    
    # Check for suspicious patterns
    if coin_id.count('-') > 10:  # Too many dashes usually indicates invalid ID
        return False
    
    return True

# =============================================================================
# INITIALIZATION AND SETUP
# =============================================================================

def initialize_session_manager():
    """Initialize the session management system"""
    logging.info("🚀 FCB v2 Session Manager initialized")
    logging.info(f"📊 Session storage ready, cleanup interval: 24 hours")
    
    # Clean any existing expired data
    cleaned = clean_expired_cache()
    if cleaned > 0:
        logging.info(f"🧹 Startup cleanup: removed {cleaned} expired cache entries")

def get_session_manager_status() -> str:
    """Get status report for session manager"""
    stats = get_session_stats()
    
    status = f"""📱 **FCB v2 Session Manager Status**

📊 **Active Sessions:** {stats['active_sessions']}/{stats['total_sessions']}
💾 **Cached Items:** {stats['total_cached_items']}
💭 **Memory Usage:** ~{stats['memory_usage_mb']} MB
🕒 **Cache TTL:** 1 hour
🧹 **Session Cleanup:** 24 hours

✅ **System Ready** - Navigation and caching operational"""
    
    return status

# Auto-initialize when module is imported
initialize_session_manager()