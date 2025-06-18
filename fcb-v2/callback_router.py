"""
FCB v2 Callback Router System - COMPLETELY FIXED
Central routing system that connects all completed systems together
"""

import logging
from typing import Dict, Any, Optional, Tuple, Union
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

# Import all completed systems
from navigation_handler import (
    process_navigation_callback,
    NavigationResult
)
from payment_handler import (
    process_payment_callback,
    PaymentResult
)
from command_handlers import (
    route_command,
    CommandResult
)
from token_economics import (
    get_user_balance_info,
    get_clean_balance_display
)
from session_manager import (
    clear_user_session,
    get_session_stats
)

logger = logging.getLogger(__name__)

# =============================================================================
# CALLBACK ROUTING RESULT CLASS
# =============================================================================

class CallbackResult:
    """Unified result object for all callback operations"""
    def __init__(self, success: bool, message: str = "", keyboard: InlineKeyboardMarkup = None,
                 parse_mode: str = 'Markdown', edit_message: bool = True, 
                 answer_callback: bool = True, show_alert: bool = False,
                 alert_text: str = ""):
        self.success = success
        self.message = message
        self.keyboard = keyboard
        self.parse_mode = parse_mode
        self.edit_message = edit_message
        self.answer_callback = answer_callback
        self.show_alert = show_alert
        self.alert_text = alert_text

# =============================================================================
# MAIN CALLBACK ROUTER CLASS - COMPLETELY FIXED
# =============================================================================

class FCBCallbackRouter:
    """
    Central callback router for FCB v2
    Routes all button callbacks to appropriate system handlers
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.route_map = self._build_route_map()
        logger.info("FCB Callback Router initialized")
    
    def _build_route_map(self) -> Dict[str, str]:
        """
        Build mapping of callback prefixes to handler systems - FIXED
        """
        return {
            # Navigation callbacks
            'nav_': 'navigation',
            
            # Payment callbacks  
            'buy_': 'payment',
            'show_buy_menu': 'payment',
            'stars_info': 'payment',
            'close_menu': 'payment',
            'retry_buy': 'payment',
            
            # Discovery callbacks - FIXED
            'start_scanning': 'discovery',
            'discover_new': 'discovery',
            
            # Command callbacks (from command handler buttons)
            'show_balance': 'balance',
            'show_help': 'command',
            'show_status': 'command',
            'refresh_balance': 'balance',
            'refresh_status': 'command',
            'show_detailed_stats': 'stats',
            'check_alerts': 'alerts',
            
            # Session management callbacks
            'clear_my_session': 'session',
            'debug_session': 'session',
            
            # External system callbacks
            'buy_coin': 'external_buy',
            'set_alert': 'external_alerts',
            'view_portfolio': 'external_portfolio'
        }
    
    async def route_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """
        Main callback routing function
        Routes callback_data to appropriate handler system
        """
        try:
            query = update.callback_query
            user_id = query.from_user.id
            callback_data = query.data
            
            logger.info(f"Routing callback: {callback_data} from user {user_id}")
            
            # Determine which system should handle this callback
            handler_system = self._determine_handler(callback_data)
            
            # Route to appropriate handler
            if handler_system == 'navigation':
                return await self._handle_navigation_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'payment':
                return await self._handle_payment_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'command':
                return await self._handle_command_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'balance':
                return await self._handle_balance_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'stats':
                return await self._handle_stats_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'session':
                return await self._handle_session_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'discovery':
                return await self._handle_discovery_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'alerts':
                return await self._handle_alerts_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'external_buy':
                return await self._handle_external_buy_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'external_alerts':
                return await self._handle_external_alerts_callback(callback_data, user_id, update, context)
            
            elif handler_system == 'external_portfolio':
                return await self._handle_external_portfolio_callback(callback_data, user_id, update, context)
            
            else:
                # Unknown callback
                logger.warning(f"Unknown callback: {callback_data} from user {user_id}")
                return CallbackResult(
                    success=False,
                    message="❌ Unknown action. Please try again.",
                    show_alert=True,
                    alert_text="Unknown button action"
                )
                
        except Exception as e:
            logger.error(f"Error routing callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ System error. Please try again.",
                show_alert=True,
                alert_text="Callback processing error"
            )
    
    def _determine_handler(self, callback_data: str) -> str:
        """
        Determine which handler system should process this callback
        """
        # Check exact matches first
        if callback_data in self.route_map:
            return self.route_map[callback_data]
        
        # Check prefix matches
        for prefix, handler in self.route_map.items():
            if callback_data.startswith(prefix):
                return handler
        
        # Default to unknown
        return 'unknown'
    
    # =============================================================================
    # NAVIGATION SYSTEM CALLBACKS
    # =============================================================================
    
    async def _handle_navigation_callback(self, callback_data: str, user_id: int,
                                        update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle navigation system callbacks"""
        try:
            # Route to navigation handler
            nav_result = await process_navigation_callback(user_id, callback_data, update, context)
            
            if nav_result.success and nav_result.coin_data:
                # ===== FCB v1 STYLE COIN DISPLAY =====
                
                # Get coin data
                coin_data = nav_result.coin_data
                symbol = coin_data.get('symbol', 'UNKNOWN').upper()
                name = coin_data.get('name', 'Unknown Token')
                price = coin_data.get('price', 0)
                
                # Get FOMO analysis
                fomo_score = coin_data.get('fomo_score', 50)
                signal = coin_data.get('signal', 'Analysis pending')
                
                # Format EXACTLY like FCB v1 screenshot
                coin_message = ""
                
                # Add coin image if available
                image_url = coin_data.get('image_url')
                if image_url:
                    coin_message += f"🖼️ [Coin Logo]({image_url})\n\n"
                
                # Coin header (EXACT FCB v1 style)
                coin_message += f"🚀 **{name} ({symbol})**\n\n"
                
                # FOMO score (EXACT FCB v1 format: "FOMO: 81.72%")
                coin_message += f"**FOMO: {fomo_score:.2f}%**\n"
                
                # Signal/analysis (EXACT FCB v1 format: "⚡ High probability opportunity")
                coin_message += f"⚡ {signal}\n\n"
                
                # Balance display (EXACT FCB v1 format: "🤖 Tokens: 0")
                balance_info = get_user_balance_info(user_id)
                coin_message += f"🤖 Tokens: {balance_info['total_scans']}\n\n"
                
                # Add navigation buttons
                from navigation_handler import get_navigation_buttons
                keyboard = get_navigation_buttons(user_id, nav_result.coin_data)
                
                return CallbackResult(
                    success=True,
                    message=coin_message,
                    keyboard=keyboard
                )
            
            elif not nav_result.success and nav_result.error_message:
                # Check if it's an "out of scans" error
                error_msg = nav_result.error_message
                
                if "No queries available" in error_msg or "insufficient scans" in error_msg.lower():
                    # FCB v1 style "Out of Scans" message
                    fcb_error_msg = "💔 **Out of Scans!**\n\n"
                    fcb_error_msg += "You wanted fresh data but you're out of scans.\n\n"
                    fcb_error_msg += "🔥 **Opportunities are moving fast!**\n\n"
                    fcb_error_msg += "💰 Get more scans with /buy"
                    
                    return CallbackResult(
                        success=False,
                        message=fcb_error_msg,
                        show_alert=False  # Show as message, not alert
                    )
                else:
                    # Regular error message
                    return CallbackResult(
                        success=False,
                        message=error_msg,
                        show_alert=True,
                        alert_text="Navigation error"
                    )
            
            else:
                # Unknown navigation result
                return CallbackResult(
                    success=False,
                    message="❌ Navigation error occurred",
                    show_alert=True,
                    alert_text="Navigation processing error"
                )
                
        except Exception as e:
            logger.error(f"Error in navigation callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Navigation system error",
                show_alert=True,
                alert_text="Navigation error"
            )
    
    # =============================================================================
    # PAYMENT SYSTEM CALLBACKS
    # =============================================================================
    
    async def _handle_payment_callback(self, callback_data: str, user_id: int,
                                     update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle payment system callbacks"""
        try:
            # Route to payment handler
            payment_result = await process_payment_callback(user_id, callback_data, update, context)
            
            if payment_result.success:
                # Payment callback processed successfully
                if payment_result.message:
                    return CallbackResult(
                        success=True,
                        message=payment_result.message,
                        edit_message=False,  # Payment handler handles message editing
                        answer_callback=True
                    )
                else:
                    return CallbackResult(
                        success=True,
                        message="✅ Payment action completed",
                        answer_callback=True
                    )
            else:
                # Payment callback failed
                return CallbackResult(
                    success=False,
                    message=payment_result.message or "❌ Payment processing error",
                    show_alert=True,
                    alert_text="Payment error"
                )
                
        except Exception as e:
            logger.error(f"Error in payment callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Payment system error",
                show_alert=True,
                alert_text="Payment error"
            )
    
    # =============================================================================
    # COMMAND SYSTEM CALLBACKS
    # =============================================================================
    
    async def _handle_command_callback(self, callback_data: str, user_id: int,
                                     update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle command-related callbacks"""
        try:
            if callback_data == 'show_help':
                # Route to help command
                command_result = await route_command('help', update, context)
                
            elif callback_data == 'show_status':
                # Route to status command
                command_result = await route_command('status', update, context)
                
            elif callback_data == 'refresh_status':
                # Refresh status display
                command_result = await route_command('status', update, context)
                
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown command action",
                    show_alert=True,
                    alert_text="Unknown command"
                )
            
            # Convert CommandResult to CallbackResult
            return CallbackResult(
                success=command_result.success,
                message=command_result.message,
                keyboard=command_result.keyboard,
                parse_mode=command_result.parse_mode
            )
            
        except Exception as e:
            logger.error(f"Error in command callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Command system error",
                show_alert=True,
                alert_text="Command error"
            )
    
    # =============================================================================
    # BALANCE SYSTEM CALLBACKS
    # =============================================================================
    
    async def _handle_balance_callback(self, callback_data: str, user_id: int,
                                     update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle balance-related callbacks"""
        try:
            if callback_data in ['show_balance', 'refresh_balance']:
                # Route to balance command
                command_result = await route_command('balance', update, context)
                
                return CallbackResult(
                    success=command_result.success,
                    message=command_result.message,
                    keyboard=command_result.keyboard,
                    parse_mode=command_result.parse_mode
                )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown balance action",
                    show_alert=True,
                    alert_text="Unknown balance action"
                )
                
        except Exception as e:
            logger.error(f"Error in balance callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Balance system error",
                show_alert=True,
                alert_text="Balance error"
            )
    
    # =============================================================================
    # STATISTICS CALLBACKS
    # =============================================================================
    
    async def _handle_stats_callback(self, callback_data: str, user_id: int,
                                   update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle statistics display callbacks"""
        try:
            if callback_data == 'show_detailed_stats':
                balance_info = get_user_balance_info(user_id)
                session_stats = get_session_stats()
                
                stats_text = "📊 **Detailed User Statistics**\n\n"
                stats_text += f"🔋 **Current Balance:**\n"
                stats_text += f"• FCB Tokens: {balance_info['fcb_balance']}\n"
                stats_text += f"• Free Scans: {balance_info['total_free_remaining']}\n"
                stats_text += f"• Total Available: {balance_info['total_scans']}\n\n"
                
                stats_text += f"📱 **Session Stats:**\n"
                stats_text += f"• Active sessions: {session_stats['active_sessions']}\n"
                stats_text += f"• Cached items: {session_stats['total_cached_items']}\n"
                stats_text += f"• Memory usage: ~{session_stats['memory_usage_mb']} MB\n\n"
                
                stats_text += "💡 Use /status for full system information"
                
                return CallbackResult(
                    success=True,
                    message=stats_text
                )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown stats action",
                    show_alert=True,
                    alert_text="Unknown stats action"
                )
                
        except Exception as e:
            logger.error(f"Error in stats callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Statistics system error",
                show_alert=True,
                alert_text="Stats error"
            )
    
    # =============================================================================
    # SESSION MANAGEMENT CALLBACKS
    # =============================================================================
    
    async def _handle_session_callback(self, callback_data: str, user_id: int,
                                     update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle session management callbacks"""
        try:
            if callback_data == 'clear_my_session':
                # Clear user's session
                clear_user_session(user_id)
                
                return CallbackResult(
                    success=True,
                    message="🧹 **Session Cleared!**\n\nYour navigation history has been reset.\nStart fresh with any command!",
                    show_alert=True,
                    alert_text="Session cleared successfully"
                )
            
            elif callback_data == 'debug_session':
                # Show debug session info (for development)
                from session_manager import debug_user_session
                debug_info = debug_user_session(user_id)
                
                return CallbackResult(
                    success=True,
                    message=f"🔧 **Debug Info:**\n```\n{debug_info}\n```",
                    parse_mode='Markdown'
                )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown session action",
                    show_alert=True,
                    alert_text="Unknown session action"
                )
                
        except Exception as e:
            logger.error(f"Error in session callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Session system error",
                show_alert=True,
                alert_text="Session error"
            )
    
    # =============================================================================
    # DISCOVERY SYSTEM CALLBACKS - COMPLETELY FIXED
    # =============================================================================
    
    async def _handle_discovery_callback(self, callback_data: str, user_id: int,
                                       update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle discovery system callbacks - FIXED"""
        try:
            if callback_data == 'discover_new' or callback_data == 'start_scanning':
                logger.info(f"🔍 Discovery triggered for user {user_id} via {callback_data}")
                
                # Check if user has scans available
                balance_info = get_user_balance_info(user_id)
                if balance_info['total_scans'] <= 0:
                    return CallbackResult(
                        success=False,
                        message="🚨 **Out of Scans!**\n\nYou wanted fresh data but you're out of scans.\n\n🔥 **Opportunities are moving fast!**\n\n💰 Get more scans with /buy",
                        show_alert=False
                    )
                
                # Trigger new coin discovery using navigation system
                nav_result = await process_navigation_callback(user_id, 'nav_next', update, context)
                
                if nav_result.success and nav_result.coin_data:
                    # Format discovered coin using FCB v1 style
                    coin_data = nav_result.coin_data
                    symbol = coin_data.get('symbol', 'UNKNOWN').upper()
                    name = coin_data.get('name', 'Unknown Token')
                    fomo_score = coin_data.get('fomo_score', 50)
                    signal = coin_data.get('signal', 'New discovery')
                    price = coin_data.get('price', 0)
                    volume = coin_data.get('volume_24h', 0)
                    
                    # FCB v1 EXACT formatting
                    coin_message = f"🚀 **{name} ({symbol})**\n\n"
                    coin_message += f"**FOMO: {fomo_score:.2f}%**\n"
                    coin_message += f"⚡ {signal}\n\n"
                    
                    # Add balance display (EXACT FCB v1 format)
                    balance_info = get_user_balance_info(user_id)
                    coin_message += f"🤖 Tokens: {balance_info['total_scans']}\n\n"
                    
                    # Add price/volume info
                    if price > 0:
                        coin_message += f"💰 Price: ${price:.8f}\n"
                    if volume > 0:
                        coin_message += f"📊 Volume: ${volume:,.0f}\n"
                    
                    # Add navigation buttons
                    from navigation_handler import get_navigation_buttons
                    keyboard = get_navigation_buttons(user_id, nav_result.coin_data)
                    
                    return CallbackResult(
                        success=True,
                        message=coin_message,
                        keyboard=keyboard
                    )
                else:
                    # Discovery failed
                    error_msg = nav_result.error_message or "🔍 No new opportunities found at this time"
                    return CallbackResult(
                        success=False,
                        message=error_msg,
                        show_alert=True,
                        alert_text="Discovery failed"
                    )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown discovery action",
                    show_alert=True,
                    alert_text="Unknown discovery action"
                )
                
        except Exception as e:
            logger.error(f"Error in discovery callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Discovery system error",
                show_alert=True,
                alert_text="Discovery error"
            )
    
    # =============================================================================
    # ALERTS SYSTEM CALLBACKS
    # =============================================================================
    
    async def _handle_alerts_callback(self, callback_data: str, user_id: int,
                                    update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle alerts system callbacks"""
        try:
            if callback_data == 'check_alerts':
                # TODO: Integrate with your alerts system
                # For now, show placeholder
                
                alerts_message = "🔔 **FCB Alerts**\n\n"
                alerts_message += "📊 Currently no active alerts\n\n"
                alerts_message += "💡 **Coming Soon:**\n"
                alerts_message += "• Price movement alerts\n"
                alerts_message += "• Volume spike alerts\n"
                alerts_message += "• Elite score alerts\n"
                alerts_message += "• Custom threshold alerts\n\n"
                alerts_message += "🚀 This feature will be integrated with your existing FCB alerts system!"
                
                return CallbackResult(
                    success=True,
                    message=alerts_message
                )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown alerts action",
                    show_alert=True,
                    alert_text="Unknown alerts action"
                )
                
        except Exception as e:
            logger.error(f"Error in alerts callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Alerts system error",
                show_alert=True,
                alert_text="Alerts error"
            )
    
    # =============================================================================
    # EXTERNAL SYSTEM CALLBACKS (FOR FUTURE INTEGRATION)
    # =============================================================================
    
    async def _handle_external_buy_callback(self, callback_data: str, user_id: int,
                                          update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle external buy system callbacks"""
        try:
            if callback_data == 'buy_coin':
                # TODO: Integrate with your external buy system
                buy_message = "💲 **Buy Coin Feature**\n\n"
                buy_message += "🚧 This feature connects to your external buy system\n\n"
                buy_message += "💡 **Integration Point:**\n"
                buy_message += "Connect this to your existing coin purchase flow\n\n"
                buy_message += "🔗 **Ready for Integration:** This callback router can easily connect to any external buy system you have!"
                
                return CallbackResult(
                    success=True,
                    message=buy_message,
                    show_alert=True,
                    alert_text="Buy system integration point"
                )
            
            else:
                return CallbackResult(
                    success=False,
                    message="❌ Unknown buy action",
                    show_alert=True,
                    alert_text="Unknown buy action"
                )
                
        except Exception as e:
            logger.error(f"Error in external buy callback {callback_data}: {e}")
            return CallbackResult(
                success=False,
                message="❌ Buy system error",
                show_alert=True,
                alert_text="Buy error"
            )
    
    async def _handle_external_alerts_callback(self, callback_data: str, user_id: int,
                                             update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle external alerts system callbacks"""
        # TODO: Integrate with your external alerts system
        return CallbackResult(
            success=True,
            message="🔔 External alerts integration point",
            show_alert=True,
            alert_text="Alerts integration ready"
        )
    
    async def _handle_external_portfolio_callback(self, callback_data: str, user_id: int,
                                                update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
        """Handle external portfolio system callbacks"""
        # TODO: Integrate with your external portfolio system
        return CallbackResult(
            success=True,
            message="📊 Portfolio integration point",
            show_alert=True,
            alert_text="Portfolio integration ready"
        )

# =============================================================================
# GLOBAL CALLBACK ROUTER INSTANCE
# =============================================================================

callback_router = FCBCallbackRouter()

# =============================================================================
# CONVENIENCE FUNCTIONS FOR MAIN BOT INTEGRATION
# =============================================================================

async def process_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> CallbackResult:
    """
    Main callback processing function for integration with main bot
    """
    return await callback_router.route_callback(update, context)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram callback query handler function
    Ready for direct integration with telegram bot
    """
    try:
        result = await process_callback_query(update, context)
        
        # Answer the callback query
        if result.answer_callback:
            await update.callback_query.answer(
                text=result.alert_text if result.show_alert else None,
                show_alert=result.show_alert
            )
        
        # Edit or send message based on result
        if result.edit_message and result.message:
            try:
                await update.callback_query.edit_message_text(
                    text=result.message,
                    reply_markup=result.keyboard,
                    parse_mode=result.parse_mode,
                    disable_web_page_preview=True
                )
            except Exception as e:
                # If editing fails, send new message
                logger.warning(f"Failed to edit message, sending new: {e}")
                await update.callback_query.message.reply_text(
                    text=result.message,
                    reply_markup=result.keyboard,
                    parse_mode=result.parse_mode,
                    disable_web_page_preview=True
                )
        
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        await update.callback_query.answer(
            text="❌ System error occurred",
            show_alert=True
        )

def get_callback_handler():
    """
    Get CallbackQueryHandler for registering with telegram bot
    """
    return CallbackQueryHandler(handle_callback_query)

# =============================================================================
# ROUTING STATISTICS AND DEBUGGING
# =============================================================================

def get_routing_stats() -> Dict[str, Any]:
    """Get callback routing statistics"""
    return {
        'total_routes': len(callback_router.route_map),
        'handler_systems': len(set(callback_router.route_map.values())),
        'route_map': callback_router.route_map
    }

def debug_routing(callback_data: str) -> Dict[str, Any]:
    """Debug callback routing for development"""
    handler = callback_router._determine_handler(callback_data)
    return {
        'callback_data': callback_data,
        'determined_handler': handler,
        'available_routes': list(callback_router.route_map.keys())
    }

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_callback_router():
    """Initialize the callback router system"""
    logger.info("🔀 FCB v2 Callback Router initialized")
    logger.info(f"📋 Total routes configured: {len(callback_router.route_map)}")
    logger.info("🔗 All systems connected and ready for callbacks")
    
    # Log route summary
    handler_counts = {}
    for handler in callback_router.route_map.values():
        handler_counts[handler] = handler_counts.get(handler, 0) + 1
    
    for handler, count in handler_counts.items():
        logger.info(f"  • {handler}: {count} routes")

# Auto-initialize when module is imported
initialize_callback_router()