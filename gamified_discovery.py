# =============================================================================
# 🎰 GAMIFIED DISCOVERY ENGINE - "Just One More Scan" Psychology
# =============================================================================

import random
import time
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional

class GamifiedDiscoveryEngine:
    """
    Addictive discovery system using proven behavioral psychology
    Creates "just one more scan" mentality while balancing free vs paid experience
    """
    
    def __init__(self):
        # 🎯 RARITY BAND SYSTEM - Based on percentile ranking
        self.rarity_bands = {
            'LEGENDARY': {
                'percentile_range': (0, 10),     # Top 10%
                'base_odds': 3,                  # 3% base chance
                'emoji': '🏆',
                'tier_name': 'LEGENDARY OPPORTUNITY',
                'message': "🎊 JACKPOT! This is exactly what you were scanning for!"
            },
            'EPIC': {
                'percentile_range': (10, 20),    # 10-20%
                'base_odds': 8,                  # 8% base chance
                'emoji': '💎',
                'tier_name': 'EPIC DISCOVERY',
                'message': "💎 EPIC DISCOVERY! This could be huge!"
            },
            'RARE': {
                'percentile_range': (20, 40),    # 20-40%
                'base_odds': 20,                 # 20% base chance
                'emoji': '⭐',
                'tier_name': 'RARE FIND',
                'message': "⭐ Nice! You're getting closer to the big ones!"
            },
            'COMMON': {
                'percentile_range': (40, 60),    # 40-60%
                'base_odds': 35,                 # 35% base chance
                'emoji': '🔷',
                'tier_name': 'SOLID OPPORTUNITY',
                'message': "🔷 Solid find! Keep scanning for better opportunities!"
            },
            'BASIC': {
                'percentile_range': (60, 100),   # 60-100%
                'base_odds': 34,                 # 34% base chance
                'emoji': '⚪',
                'tier_name': 'BASIC DISCOVERY',
                'message': "🎯 Almost there! Your next scan could be LEGENDARY!"
            }
        }
        
        # 🎁 PSYCHOLOGICAL MULTIPLIERS - Proven gambling mechanics
        self.multipliers = {
            'daily_first_scan': 1.8,      # Brings users back daily
            'early_session': 1.5,         # Hooks new sessions (scans 1-3)
            'pity_system': 3.0,           # Prevents rage quit (8+ bad scans)
            'premium_user': 1.3,          # Rewards paying customers
            'free_scan_penalty': 0.85,    # Encourages token purchases
            'desperation_bonus': 2.0      # Anti-frustration (15+ scans)
        }
        
        # 📊 SESSION TRACKING - For psychology mechanics
        self.user_sessions = {}
    
    def get_user_session(self, user_id: int) -> Dict:
        """Get or create user session for psychology tracking"""
        current_time = time.time()
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'scans_today': 0,
                'consecutive_bad_scans': 0,
                'total_session_scans': 0,
                'last_scan_time': current_time,
                'last_legendary': None,
                'is_premium': False,
                'daily_reset': datetime.now().date()
            }
        
        session = self.user_sessions[user_id]
        
        # Daily reset check
        if session['daily_reset'] != datetime.now().date():
            session['scans_today'] = 0
            session['consecutive_bad_scans'] = 0
            session['total_session_scans'] = 0
            session['daily_reset'] = datetime.now().date()
            logging.info(f"🌅 Daily reset for user {user_id}")
        
        # Session timeout (2 hours = new session)
        if current_time - session['last_scan_time'] > 7200:
            session['total_session_scans'] = 0
            logging.info(f"🔄 New session started for user {user_id}")
        
        session['last_scan_time'] = current_time
        return session
    
    def update_premium_status(self, user_id: int, is_premium: bool):
        """Update user's premium status for bonuses"""
        session = self.get_user_session(user_id)
        session['is_premium'] = is_premium
        logging.info(f"👑 Premium status updated: User {user_id} = {is_premium}")
    
    def calculate_dynamic_odds(self, user_id: int, rarity_band: str, is_free_scan: bool = False) -> float:
        """
        Calculate dynamic odds with all psychological multipliers
        This is where the magic happens!
        """
        session = self.get_user_session(user_id)
        base_odds = self.rarity_bands[rarity_band]['base_odds']
        
        # Start with base odds
        final_odds = base_odds
        multiplier_details = []
        
        # 🎁 DAILY FIRST SCAN BONUS (brings users back daily)
        if session['scans_today'] == 0:
            final_odds *= self.multipliers['daily_first_scan']
            multiplier_details.append(f"Daily First: {self.multipliers['daily_first_scan']}x")
        
        # 🔥 EARLY SESSION BONUS (hooks new sessions)
        elif session['total_session_scans'] <= 3:
            final_odds *= self.multipliers['early_session']
            multiplier_details.append(f"Early Session: {self.multipliers['early_session']}x")
        
        # 💰 PITY SYSTEM (prevents rage quit)
        if session['consecutive_bad_scans'] >= 8:
            final_odds *= self.multipliers['pity_system']
            multiplier_details.append(f"Pity System: {self.multipliers['pity_system']}x")
        
        # 😤 DESPERATION BONUS (anti-frustration)
        elif session['consecutive_bad_scans'] >= 15:
            final_odds *= self.multipliers['desperation_bonus']
            multiplier_details.append(f"Desperation: {self.multipliers['desperation_bonus']}x")
        
        # 👑 PREMIUM USER BONUS
        if session.get('is_premium', False):
            final_odds *= self.multipliers['premium_user']
            multiplier_details.append(f"Premium: {self.multipliers['premium_user']}x")
        
        # 💸 FREE SCAN PENALTY (encourages token purchases)
        if is_free_scan:
            final_odds *= self.multipliers['free_scan_penalty']
            multiplier_details.append(f"Free Scan: {self.multipliers['free_scan_penalty']}x")
        
        # Log the multiplier calculation for debugging
        if multiplier_details:
            logging.info(f"🎯 Odds for {rarity_band}: {base_odds}% → {final_odds:.1f}% ({', '.join(multiplier_details)})")
        
        return final_odds
    
    def select_rarity_tier(self, user_id: int, is_free_scan: bool = False) -> str:
        """
        Select rarity tier using dynamic psychology-based odds
        This determines what quality of coin the user gets
        """
        # Calculate dynamic odds for each tier
        tier_odds = {}
        total_weight = 0
        
        for tier_name in self.rarity_bands.keys():
            odds = self.calculate_dynamic_odds(user_id, tier_name, is_free_scan)
            tier_odds[tier_name] = odds
            total_weight += odds
        
        # Normalize to create probability distribution
        normalized_odds = {tier: odds/total_weight for tier, odds in tier_odds.items()}
        
        # Use weighted random selection
        rand = random.random()
        cumulative = 0
        
        for tier_name, probability in normalized_odds.items():
            cumulative += probability
            if rand <= cumulative:
                logging.info(f"🎰 Selected tier: {tier_name} (prob: {probability:.1%})")
                return tier_name
        
        # Fallback (should never reach here)
        return 'COMMON'
    
    def select_coin_from_tier(self, cached_coins: List[Dict], rarity_tier: str) -> Optional[Dict]:
        """
        Select a specific coin from the chosen rarity tier
        Uses percentile ranking to determine which coins belong to which tier
        """
        if not cached_coins:
            return None
        
        # Get tier parameters
        tier_config = self.rarity_bands[rarity_tier]
        start_percentile, end_percentile = tier_config['percentile_range']
        
        # Calculate the actual coin range based on percentiles
        total_coins = len(cached_coins)
        start_index = int((start_percentile / 100) * total_coins)
        end_index = int((end_percentile / 100) * total_coins)
        
        # Ensure we don't go out of bounds
        start_index = max(0, min(start_index, total_coins - 1))
        end_index = max(start_index + 1, min(end_index, total_coins))
        
        # Select coins in this tier
        tier_coins = cached_coins[start_index:end_index]
        
        if not tier_coins:
            # Fallback to any available coin
            return random.choice(cached_coins)
        
        # Random selection within the tier
        selected_coin = random.choice(tier_coins)
        
        logging.info(f"🎯 Selected from {rarity_tier} tier: {selected_coin.get('symbol', 'Unknown')} (index {start_index}-{end_index})")
        
        return selected_coin
    
    def get_excitement_message(self, rarity_tier: str, coin_symbol: str) -> str:
        """
        Get psychology-driven excitement message
        CRITICAL: NO spending notifications - only joy and anticipation!
        The token meter handles balance changes silently for pure addiction psychology
        """
        tier_config = self.rarity_bands[rarity_tier]
        base_message = tier_config['message']
        tier_name = tier_config['tier_name']
        
        # Add coin-specific excitement for high tiers with clear context
        if rarity_tier == 'LEGENDARY':
            messages = [
                f"🎊 LEGENDARY OPPORTUNITY! {coin_symbol} is exactly what you were looking for!",
                f"🏆 LEGENDARY FIND! {coin_symbol} has massive potential!",
                f"🎯 LEGENDARY DISCOVERY! This {coin_symbol} could be life-changing!"
            ]
            return random.choice(messages)
        
        elif rarity_tier == 'EPIC':
            messages = [
                f"💎 EPIC OPPORTUNITY! {coin_symbol} looks absolutely incredible!",
                f"⚡ EPIC DISCOVERY! {coin_symbol} has serious potential!",
                f"🚀 EPIC FIND! {coin_symbol} could be the one!"
            ]
            return random.choice(messages)
        
        elif rarity_tier == 'RARE':
            messages = [
                f"⭐ RARE OPPORTUNITY! {coin_symbol} is looking promising!",
                f"🌟 RARE FIND! {coin_symbol} has good potential!",
                f"✨ RARE DISCOVERY! {coin_symbol} caught our scanner!"
            ]
            return random.choice(messages)
        
        # For COMMON and BASIC, use base message with clear context
        if rarity_tier == 'COMMON':
            return f"🔷 SOLID OPPORTUNITY! {coin_symbol} - {base_message}"
        elif rarity_tier == 'BASIC':
            return f"⚪ BASIC DISCOVERY! {coin_symbol} - {base_message}"
        
        # Fallback with tier name for clarity
        return f"{tier_config['emoji']} {tier_name}! {base_message}"
    
    def update_session_after_scan(self, user_id: int, rarity_tier: str):
        """
        Update session statistics after a scan
        This drives the psychology mechanics
        """
        session = self.get_user_session(user_id)
        
        # Update counters
        session['scans_today'] += 1
        session['total_session_scans'] += 1
        
        # Update streak tracking
        if rarity_tier in ['LEGENDARY', 'EPIC']:
            # Good result - reset bad streak
            session['consecutive_bad_scans'] = 0
            if rarity_tier == 'LEGENDARY':
                session['last_legendary'] = time.time()
            logging.info(f"🎉 Good result for user {user_id}: {rarity_tier} (streak reset)")
        else:
            # Increase bad streak for psychology mechanics
            session['consecutive_bad_scans'] += 1
            logging.info(f"📈 Bad streak for user {user_id}: {session['consecutive_bad_scans']} consecutive")
    
    def gamified_discovery(self, user_id: int, cached_coins: List[Dict], is_free_scan: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
        """
        MAIN FUNCTION: Execute gamified discovery with full psychology
        
        Returns: (selected_coin, excitement_message)
        """
        if not cached_coins:
            return None, None
        
        # Step 1: Select rarity tier using psychology
        rarity_tier = self.select_rarity_tier(user_id, is_free_scan)
        
        # Step 2: Select specific coin from that tier
        selected_coin = self.select_coin_from_tier(cached_coins, rarity_tier)
        
        if not selected_coin:
            return None, None
        
        # Step 3: Generate excitement message
        coin_symbol = selected_coin.get('symbol', 'Unknown')
        excitement_message = self.get_excitement_message(rarity_tier, coin_symbol)
        
        # Step 4: Update session for psychology mechanics
        self.update_session_after_scan(user_id, rarity_tier)
        
        # Step 5: Enhanced logging
        session = self.get_user_session(user_id)
        fomo_score = selected_coin.get('fomo_score', 0)
        
        logging.info(f"🎰 GAMIFIED DISCOVERY for User {user_id}:")
        logging.info(f"   Tier: {rarity_tier} | Coin: {coin_symbol} | FOMO: {fomo_score}")
        logging.info(f"   Session: {session['total_session_scans']} scans, {session['consecutive_bad_scans']} bad streak")
        logging.info(f"   Message: {excitement_message}")
        logging.info(f"   🎯 PSYCHOLOGY: Pure excitement delivery - no spending friction!")
        logging.info(f"   🪙 TOKEN ECONOMY: 10 Stars = 1 Token = 1 Premium Scan")
        
        return selected_coin, excitement_message

# =============================================================================
# 🔄 INTEGRATION FUNCTIONS - Replace existing functions
# =============================================================================

# Initialize the gamified engine (singleton)
gamified_engine = GamifiedDiscoveryEngine()

def hunt_next_opportunity_gamified(cached_coins: List[Dict], user_id: int = None, is_free_scan: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    """
    REPLACEMENT for existing hunt_next_opportunity function
    Now with full gamification and psychology!
    
    Args:
        cached_coins: List of available coins sorted by ranking
        user_id: User ID for psychology tracking 
        is_free_scan: Whether this is a free scan (affects odds)
    
    Returns:
        (selected_coin, excitement_message)
    """
    if user_id is None:
        # Fallback to simple random if no user_id
        if cached_coins:
            return random.choice(cached_coins), None
        return None, None
    
    # Use the gamified engine
    return gamified_engine.gamified_discovery(user_id, cached_coins, is_free_scan)

def update_premium_user_status(user_id: int, is_premium: bool):
    """
    Update user's premium status for bonus odds
    Call this after successful payment
    """
    gamified_engine.update_premium_status(user_id, is_premium)

def get_user_psychology_stats(user_id: int) -> Dict:
    """
    Get user's psychology statistics for debugging/analytics
    """
    session = gamified_engine.get_user_session(user_id)
    return {
        'scans_today': session['scans_today'],
        'session_scans': session['total_session_scans'],
        'bad_streak': session['consecutive_bad_scans'],
        'is_premium': session.get('is_premium', False),
        'time_since_legendary': time.time() - session['last_legendary'] if session['last_legendary'] else None
    }

# =============================================================================
# 🧪 TESTING FUNCTIONS
# =============================================================================

def test_gamified_discovery():
    """Test the gamified discovery system"""
    
    # Mock cached coins data
    mock_coins = []
    for i in range(100):
        mock_coins.append({
            'coin': f'coin-{i}',
            'symbol': f'COIN{i}',
            'fomo_score': 100 - i,  # Higher ranked coins have higher scores
            'signal_type': 'Test Signal'
        })
    
    # Test multiple discoveries for a user
    test_user_id = 12345
    
    print("🧪 Testing Gamified Discovery System")
    print("=" * 50)
    
    for scan_num in range(10):
        is_free = scan_num % 3 == 0  # Every 3rd scan is free
        
        coin, message = hunt_next_opportunity_gamified(mock_coins, test_user_id, is_free)
        
        if coin:
            print(f"Scan {scan_num + 1}: {coin['symbol']} (FOMO: {coin['fomo_score']}) {'[FREE]' if is_free else '[PAID]'}")
            if message:
                print(f"   Message: {message}")
        
        # Show psychology stats every few scans
        if scan_num % 3 == 2:
            stats = get_user_psychology_stats(test_user_id)
            print(f"   Stats: {stats['session_scans']} scans, {stats['bad_streak']} bad streak, Premium: {stats['is_premium']}")
            print()
    
    print("✅ Test completed!")

def simulate_user_journey():
    """Simulate a full user journey with psychology mechanics"""
    
    # Create realistic coin data
    mock_coins = []
    for i in range(50):
        mock_coins.append({
            'coin': f'crypto-{i}',
            'symbol': f'CRYPTO{i}',
            'fomo_score': max(10, 95 - i * 1.5),  # Graduated scoring
            'signal_type': 'Momentum' if i < 10 else 'Building' if i < 25 else 'Watch'
        })
    
    test_user = 67890
    
    print("🎭 Simulating User Journey with Psychology")
    print("=" * 50)
    
    # Day 1: New user, gets great results
    print("📅 DAY 1 - New User Experience")
    for i in range(3):
        coin, message = hunt_next_opportunity_gamified(mock_coins, test_user, is_free=(i==0))
        print(f"  Scan {i+1}: {coin['symbol']} - {message}")
    
    # Simulate bad streak
    print("\n😤 Simulating Bad Streak (pity system activation)")
    for i in range(8):
        coin, message = hunt_next_opportunity_gamified(mock_coins, test_user, False)
        if i == 7:  # Should trigger pity system
            print(f"  Scan {i+1}: {coin['symbol']} - {message} [PITY ACTIVATED]")
    
    # Test premium bonus
    print("\n👑 User Purchases Premium")
    update_premium_user_status(test_user, True)
    
    for i in range(2):
        coin, message = hunt_next_opportunity_gamified(mock_coins, test_user, False)
        print(f"  Premium Scan {i+1}: {coin['symbol']} - {message}")
    
    # Final stats
    stats = get_user_psychology_stats(test_user)
    print(f"\n📊 Final Stats: {stats}")
    print("✅ Journey simulation completed!")

if __name__ == "__main__":
    # Run tests
    test_gamified_discovery()
    print()
    simulate_user_journey()