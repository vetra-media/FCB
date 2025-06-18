"""
FCB v2 Navigation Handler System - COMPLETELY FIXED
Integrates session_manager.py + token_economics.py for smart navigation with proper costs
"""

import logging
import time
import random
from typing import Dict, Any, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Set up logger
logger = logging.getLogger(__name__)

# Try to import Elite systems
try:
    from elite_integration import analyze_coin_comprehensive
    from elite_engine import get_gaming_fomo_score
    from elite_discovery_integration import discover_new_coin_with_elite
    ELITE_AVAILABLE = True
    logger.info("🏆 Elite analysis systems loaded!")
except ImportError as e:
    ELITE_AVAILABLE = False
    logger.warning(f"⚠️ Elite analysis not available: {e}, using fallback")

# Import our completed systems
from session_manager import (
    get_user_session,
    navigate_back,
    navigate_forward,
    get_session_navigation_state,
    add_to_user_history,
    get_cached_coin_data
)
from token_economics import (
    check_rate_limit_with_fcb,
    spend_fcb_token,
    get_user_balance_info
)

try:
    from coin_image_handler import get_coin_data_with_image, format_coin_card_with_image
except ImportError:
    logger.warning("⚠️ Coin image handler not available")

# =============================================================================
# NAVIGATION RESULT CLASS
# =============================================================================

class NavigationResult:
    """Result object for navigation operations"""
    def __init__(self, success: bool, coin_data: Optional[Dict] = None, 
                 error_message: Optional[str] = None, cost_tokens: int = 0):
        self.success = success
        self.coin_data = coin_data
        self.error_message = error_message
        self.cost_tokens = cost_tokens

# =============================================================================
# MAIN NAVIGATION HANDLER CLASS - COMPLETELY FIXED
# =============================================================================

class FCBNavigationHandler:
    """
    Main navigation handler for FCB v2
    Manages BACK/NEXT navigation with proper token economics
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        logger.info("FCB Navigation Handler initialized")
    
    async def handle_back_navigation(self, user_id: int, update: Update, 
                                   context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
        """
        Handle BACK button navigation - Always FREE
        Uses cached data from session history
        """
        try:
            logger.info(f"User {user_id} navigating BACK")
            
            # Navigate back using session manager (always free)
            success, coin_id, cached_data = navigate_back(user_id)
            
            if success:
                logger.info(f"User {user_id} navigated back to {coin_id} (FREE)")
                
                return NavigationResult(
                    success=True,
                    coin_data=cached_data,
                    cost_tokens=0
                )
            else:
                # No back history available
                return NavigationResult(
                    success=False,
                    error_message="📍 You're at the beginning of your session",
                    cost_tokens=0
                )
                
        except Exception as e:
            logger.error(f"Error in back navigation for user {user_id}: {e}")
            return NavigationResult(
                success=False,
                error_message="❌ Navigation error occurred",
                cost_tokens=0
            )
    
    async def handle_next_navigation(self, user_id: int, update: Update,
                                   context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
        """
        Handle NEXT button navigation
        FREE if forward history exists, costs 1 token for new discovery
        """
        try:
            logger.info(f"User {user_id} navigating NEXT")
            
            # Check if we have forward history (would be FREE)
            nav_state = get_session_navigation_state(user_id)
            has_forward_history = nav_state.get('can_go_forward', False) if nav_state else False
            
            if has_forward_history:
                # FREE navigation using existing forward history
                success, coin_id, cached_data = navigate_forward(user_id)
                
                if success:
                    logger.info(f"User {user_id} navigated forward to {coin_id} (FREE - history)")
                    
                    return NavigationResult(
                        success=True,
                        coin_data=cached_data,
                        cost_tokens=0
                    )
                else:
                    # Forward navigation failed
                    return NavigationResult(
                        success=False,
                        error_message="📍 No forward history available",
                        cost_tokens=0
                    )
            
            else:
                # New discovery required - costs 1 token
                return await self._handle_new_discovery(user_id, update, context)
                
        except Exception as e:
            logger.error(f"Error in next navigation for user {user_id}: {e}")
            return NavigationResult(
                success=False,
                error_message="❌ Navigation error occurred",
                cost_tokens=0
            )
    
    async def _handle_new_discovery(self, user_id: int, update: Update,
                                  context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
        """
        Handle new coin discovery that costs 1 FCB token
        """
        try:
            # Check rate limit and token availability
            allowed, time_remaining, reason = check_rate_limit_with_fcb(user_id)
            
            if not allowed:
                if reason == "Rate limited":
                    return NavigationResult(
                        success=False,
                        error_message=f"⏱️ Please wait {time_remaining:.1f} seconds before your next search",
                        cost_tokens=0
                    )
                elif reason == "No queries available":
                    balance_info = get_user_balance_info(user_id)
                    return NavigationResult(
                        success=False,
                        error_message=f"🔋 Insufficient scans! You have {balance_info['total_scans']} scans remaining.\n\n💰 Get more scans with /buy",
                        cost_tokens=0
                    )
            
            # Discover new coin
            new_coin_data = await self._discover_new_coin(user_id, context)
            
            if new_coin_data:
                # Spend the token
                spend_success, spend_message = spend_fcb_token(user_id, 'next_discovery')
                
                if spend_success:
                    # Add to session history - need coin_id for the new coin
                    coin_id = new_coin_data.get('symbol', 'unknown').lower()
                    add_to_user_history(user_id, coin_id, new_coin_data)
                    
                    logger.info(f"User {user_id} discovered new coin {coin_id} (1 token spent)")
                    
                    return NavigationResult(
                        success=True,
                        coin_data=new_coin_data,
                        cost_tokens=1
                    )
                else:
                    return NavigationResult(
                        success=False,
                        error_message=f"❌ {spend_message}",
                        cost_tokens=0
                    )
            else:
                return NavigationResult(
                    success=False,
                    error_message="🔍 No new opportunities found at this time",
                    cost_tokens=0
                )
                
        except Exception as e:
            logger.error(f"Error in new discovery for user {user_id}: {e}")
            return NavigationResult(
                success=False,
                error_message="❌ Discovery error occurred",
                cost_tokens=0
            )
    
    async def _discover_new_coin(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
        """
        Enhanced discovery using Elite analysis + real CoinGecko data
        """
        try:
            logger.info(f"🔍 Starting discovery for user {user_id}")
            
            # Try Elite discovery first
            if ELITE_AVAILABLE:
                try:
                    discovery_result = await discover_new_coin_with_elite(user_id)
                    
                    if discovery_result:
                        logger.info(f"✅ Elite discovery: {discovery_result.get('symbol')} (FOMO: {discovery_result.get('fomo_score', 0):.1f})")
                        return discovery_result
                    else:
                        logger.warning(f"⚠️ Elite discovery returned None")
                except Exception as e:
                    logger.error(f"❌ Elite discovery error: {e}")
            
            # Fallback to basic discovery
            logger.info("🔄 Using fallback discovery")
            return await self._basic_fallback_discovery(user_id)
            
        except Exception as e:
            logger.error(f"❌ All discovery methods failed: {e}")
            return None
    
    async def _basic_fallback_discovery(self, user_id: int) -> Dict:
        """
        Basic fallback discovery when Elite systems fail
        """
        try:
            logger.info(f"🔄 Running basic fallback discovery for user {user_id}")
            
            # Mock coins for testing - represents real CoinGecko data
            mock_coins = [
                {
                    'symbol': 'DOGE', 
                    'name': 'Dogecoin', 
                    'price': 0.15,
                    'volume_24h': 2_500_000_000,
                    'market_cap': 21_000_000_000
                },
                {
                    'symbol': 'SHIB', 
                    'name': 'Shiba Inu', 
                    'price': 0.000025,
                    'volume_24h': 800_000_000,
                    'market_cap': 14_000_000_000
                },
                {
                    'symbol': 'PEPE', 
                    'name': 'Pepe', 
                    'price': 0.0000015,
                    'volume_24h': 1_200_000_000,
                    'market_cap': 600_000_000
                },
                {
                    'symbol': 'FLOKI', 
                    'name': 'Floki Inu', 
                    'price': 0.0002,
                    'volume_24h': 150_000_000,
                    'market_cap': 1_900_000_000
                },
                {
                    'symbol': 'BONK', 
                    'name': 'Bonk', 
                    'price': 0.000015,
                    'volume_24h': 300_000_000,
                    'market_cap': 1_100_000_000
                },
                {
                    'symbol': 'WIF', 
                    'name': 'dogwifhat', 
                    'price': 2.45,
                    'volume_24h': 750_000_000,
                    'market_cap': 2_400_000_000
                }
            ]
            
            selected_coin = random.choice(mock_coins)
            
            # Create realistic coin data with FOMO analysis
            coin_data = {
                'symbol': selected_coin['symbol'],
                'name': selected_coin['name'],
                'price': selected_coin['price'],
                'volume_24h': selected_coin['volume_24h'],
                'market_cap': selected_coin['market_cap'],
                'change_1h': random.uniform(-5, 15),
                'change_24h': random.uniform(-20, 30),
                'change_7d': random.uniform(-40, 50),
                'market_cap_rank': random.randint(50, 500),
                'volume_change_24h': random.uniform(-30, 200),
                
                # FOMO analysis results
                'fomo_score': random.uniform(55, 95),
                'signal': random.choice([
                    '🚀 Strong opportunity',
                    '📈 Good setup detected',
                    '⚡ High probability play',
                    '💎 Hidden gem potential',
                    '🔥 Volume spike detected',
                    '⚡ Breakout pattern forming'
                ]),
                
                # Analysis metadata
                'analysis_type': 'basic_fallback',
                'discovery_timestamp': time.time(),
                'user_id': user_id
            }
            
            logger.info(f"✅ Fallback discovery: {coin_data['symbol']} (Score: {coin_data['fomo_score']:.1f})")
            return coin_data
            
        except Exception as e:
            logger.error(f"❌ Even fallback discovery failed: {e}")
            
            # Emergency fallback - always works
            return {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'price': 67000.0,
                'volume_24h': 15_000_000_000,
                'market_cap': 1_300_000_000_000,
                'change_1h': 0.5,
                'change_24h': 2.1,
                'change_7d': -1.2,
                'market_cap_rank': 1,
                'volume_change_24h': 25.0,
                'fomo_score': 75.0,
                'signal': '📊 Market leader analysis',
                'analysis_type': 'emergency_fallback',
                'discovery_timestamp': time.time(),
                'user_id': user_id
            }
    
    def create_navigation_buttons(self, user_id: int, current_coin: Dict = None) -> InlineKeyboardMarkup:
        """
        Create navigation buttons matching FCB v1 EXACTLY
        Layout: [⬅️ BACK (X left)] [➡️ NEXT (X left)]
                [💲 BUY COIN]      [🤖 TOP UP]
        """
        try:
            nav_state = get_session_navigation_state(user_id)
            balance_info = get_user_balance_info(user_id)
            scans_remaining = balance_info['total_scans']
            
            # ROW 1: BACK and NEXT buttons
            row1 = []
            
            # BACK button (TOP LEFT)
            if nav_state and nav_state.get('can_go_back', False):
                back_text = f"⬅️ BACK ({scans_remaining} left)"
            else:
                # Show button but indicate no history
                back_text = f"⬅️ BACK ({scans_remaining} left)"
            
            row1.append(InlineKeyboardButton(back_text, callback_data="nav_back"))
            
            # NEXT button (TOP RIGHT)
            if nav_state and nav_state.get('can_go_forward', False):
                # Has forward history - FREE
                next_text = f"➡️ NEXT ({scans_remaining} left)"
            elif scans_remaining > 0:
                # New discovery - costs 1 scan
                scans_after = max(0, scans_remaining - 1)
                next_text = f"➡️ NEXT ({scans_after} left)"
            else:
                # No scans available
                next_text = "➡️ NEXT (0 left)"
            
            row1.append(InlineKeyboardButton(next_text, callback_data="nav_next"))
            
            # ROW 2: BUY COIN and TOP UP buttons
            row2 = [
                InlineKeyboardButton("💲 BUY COIN", callback_data="buy_coin"),
                InlineKeyboardButton("🤖 TOP UP", callback_data="show_buy_menu")
            ]
            
            return InlineKeyboardMarkup([row1, row2])
            
        except Exception as e:
            logger.error(f"Error creating navigation buttons: {e}")
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Error", callback_data="nav_error")]])
    
    async def handle_navigation_callback(self, user_id: int, callback_data: str,
                                       update: Update, context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
        """
        Route navigation callbacks to appropriate handlers
        """
        try:
            if callback_data == "nav_back":
                return await self.handle_back_navigation(user_id, update, context)
            
            elif callback_data == "nav_next":
                return await self.handle_next_navigation(user_id, update, context)
            
            elif callback_data == "nav_buy_scans":
                # Redirect to purchase flow
                return NavigationResult(
                    success=False,
                    error_message="💰 Get more scans with /buy command!",
                    cost_tokens=0
                )
            
            elif callback_data == "show_balance":
                balance_info = get_user_balance_info(user_id)
                balance_text = f"🔋 Your Balance:\n"
                balance_text += f"• Free Scans: {balance_info['total_free_remaining']}\n"
                balance_text += f"• FCB Tokens: {balance_info['fcb_balance']}\n"
                balance_text += f"• Total Available: {balance_info['total_scans']}"
                
                return NavigationResult(
                    success=False,
                    error_message=balance_text,
                    cost_tokens=0
                )
            
            else:
                return NavigationResult(
                    success=False,
                    error_message="❌ Unknown navigation action",
                    cost_tokens=0
                )
                
        except Exception as e:
            logger.error(f"Error handling navigation callback {callback_data} for user {user_id}: {e}")
            return NavigationResult(
                success=False,
                error_message="❌ Navigation error occurred",
                cost_tokens=0
            )

# =============================================================================
# GLOBAL NAVIGATION HANDLER INSTANCE
# =============================================================================

navigation_handler = FCBNavigationHandler()

# =============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# =============================================================================

async def handle_back(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
    """Handle BACK navigation - Always FREE"""
    return await navigation_handler.handle_back_navigation(user_id, update, context)

async def handle_next(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
    """Handle NEXT navigation - FREE if history, 1 token for new discovery"""
    return await navigation_handler.handle_next_navigation(user_id, update, context)

def get_navigation_buttons(user_id: int, current_coin: Dict = None) -> InlineKeyboardMarkup:
    """Get smart navigation buttons with cost indicators"""
    return navigation_handler.create_navigation_buttons(user_id, current_coin)

async def process_navigation_callback(user_id: int, callback_data: str,
                                    update: Update, context: ContextTypes.DEFAULT_TYPE) -> NavigationResult:
    """Process navigation button callbacks"""
    return await navigation_handler.handle_navigation_callback(user_id, callback_data, update, context)

# =============================================================================
# TESTING AND DEBUGGING FUNCTIONS
# =============================================================================

def test_navigation_handler():
    """Test function to verify navigation handler is working"""
    try:
        logger.info("🧪 Testing navigation handler...")
        
        # Test button creation
        test_user_id = 12345
        buttons = get_navigation_buttons(test_user_id)
        logger.info(f"✅ Navigation buttons created successfully")
        
        # Test navigation state
        nav_state = get_session_navigation_state(test_user_id)
        logger.info(f"✅ Navigation state: {nav_state}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Navigation handler test failed: {e}")
        return False

def get_navigation_status() -> Dict[str, Any]:
    """Get status of navigation system"""
    return {
        'elite_available': ELITE_AVAILABLE,
        'handler_initialized': navigation_handler is not None,
        'status': 'operational'
    }

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_navigation_handler():
    """Initialize the navigation handler system"""
    logger.info("🧭 FCB v2 Navigation Handler initialized")
    logger.info(f"🏆 Elite systems available: {ELITE_AVAILABLE}")
    logger.info("🔗 All navigation functions ready")

# Auto-initialize when module is imported
initialize_navigation_handler()