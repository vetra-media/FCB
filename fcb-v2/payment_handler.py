"""
FCB v2 Payment System - Telegram Stars Integration
Complete payment processing for FCB token purchases
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Import our completed systems
from token_economics import (
    add_fcb_tokens,
    record_purchase,
    get_user_balance_info,
    FCB_STAR_PACKAGES,
    update_user_activity
)
from session_manager import get_user_session

logger = logging.getLogger(__name__)

# =============================================================================
# PAYMENT SYSTEM CONSTANTS
# =============================================================================

# Payment provider token (you'll need to set this up with BotFather)
PROVIDER_TOKEN = "YOUR_TELEGRAM_PAYMENT_PROVIDER_TOKEN"  # Replace with actual token

# Payment success/failure messages
PAYMENT_MESSAGES = {
    'success': "🎉 **Payment Successful!**\n\n💰 {tokens} FCB tokens added to your account!\n🔋 Total scans available: {total_scans}\n\n✨ Thanks for supporting FCB! Start scanning with any command.",
    'cancelled': "❌ Payment cancelled. No charges made.\n\n💡 You can try again anytime with /buy",
    'failed': "❌ Payment failed. Please try again or contact support.\n\n🔄 Use /buy to retry your purchase",
    'invalid': "❌ Invalid payment data received.\n\n🛡️ For security, this payment was not processed."
}

# =============================================================================
# PAYMENT RESULT CLASS
# =============================================================================

class PaymentResult:
    """Result object for payment operations"""
    def __init__(self, success: bool, message: str = "", tokens_added: int = 0, 
                 new_balance: int = 0, package_info: Dict = None):
        self.success = success
        self.message = message
        self.tokens_added = tokens_added
        self.new_balance = new_balance
        self.package_info = package_info or {}

# =============================================================================
# MAIN PAYMENT HANDLER CLASS
# =============================================================================

class FCBPaymentHandler:
    """
    Main payment handler for FCB v2
    Manages Telegram Stars payments and FCB token delivery
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.pending_payments = {}  # Track pending payments {user_id: package_info}
        logger.info("FCB Payment Handler initialized")
    
    def create_purchase_menu(self, user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create purchase menu with available FCB token packages
        """
        try:
            # Get current user balance for context
            balance_info = get_user_balance_info(user_id)
            
            # Build menu message
            menu_text = "💰 **FCB Token Store**\n\n"
            menu_text += f"🔋 Current Balance: {balance_info['total_scans']} scans\n"
            menu_text += f"• Free Scans: {balance_info['total_free_remaining']}\n"
            menu_text += f"• FCB Tokens: {balance_info['fcb_balance']}\n\n"
            menu_text += "📦 **Available Packages:**\n\n"
            
            # Create package buttons
            keyboard = []
            
            for package_key, package_info in FCB_STAR_PACKAGES.items():
                stars = package_info['stars']
                tokens = package_info['tokens']
                title = package_info['title']
                
                # Add package description to menu
                menu_text += f"⭐ **{title}**\n"
                menu_text += f"   💳 {stars} Telegram Stars → {tokens} FCB Tokens\n"
                menu_text += f"   📱 {package_info['description']}\n\n"
                
                # Create purchase button
                button_text = f"⭐ {stars} Stars → {tokens} Tokens"
                button = InlineKeyboardButton(
                    button_text,
                    callback_data=f"buy_{package_key}"
                )
                keyboard.append([button])
            
            # Add info and close buttons
            keyboard.append([
                InlineKeyboardButton("ℹ️ About Telegram Stars", callback_data="stars_info"),
                InlineKeyboardButton("❌ Close", callback_data="close_menu")
            ])
            
            menu_text += "💡 **Why FCB Tokens?**\n"
            menu_text += "• Unlimited premium crypto scans\n"
            menu_text += "• Priority discovery alerts\n"
            menu_text += "• Advanced market analysis\n"
            menu_text += "• No daily limits\n\n"
            menu_text += "🔒 Secure payments via Telegram Stars"
            
            return menu_text, InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error creating purchase menu for user {user_id}: {e}")
            error_text = "❌ Error loading store. Please try /buy again."
            error_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Retry", callback_data="retry_buy")
            ]])
            return error_text, error_keyboard
    
    async def handle_package_selection(self, user_id: int, package_key: str,
                                     update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
        """
        Handle user selecting a package for purchase
        """
        try:
            if package_key not in FCB_STAR_PACKAGES:
                return PaymentResult(
                    success=False,
                    message="❌ Invalid package selected. Please try again."
                )
            
            package_info = FCB_STAR_PACKAGES[package_key]
            stars_amount = package_info['stars']
            tokens_amount = package_info['tokens']
            title = package_info['title']
            
            # Store pending payment info
            self.pending_payments[user_id] = {
                'package_key': package_key,
                'package_info': package_info,
                'timestamp': time.time()
            }
            
            # Create payment invoice
            prices = [LabeledPrice(label=title, amount=stars_amount)]
            
            # Send invoice
            await context.bot.send_invoice(
                chat_id=user_id,
                title=f"FCB {title}",
                description=f"Purchase {tokens_amount} FCB tokens for premium crypto scanning",
                payload=f"fcb_tokens_{package_key}_{user_id}_{int(time.time())}",
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # Telegram Stars currency
                prices=prices,
                photo_url="https://i.imgur.com/fcb_logo.png",  # Replace with your logo
                photo_width=512,
                photo_height=512,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                is_flexible=False,
                start_parameter=f"buy_{package_key}"
            )
            
            logger.info(f"Payment invoice sent to user {user_id} for package {package_key}")
            
            return PaymentResult(
                success=True,
                message=f"💳 Payment invoice sent for {title}",
                package_info=package_info
            )
            
        except TelegramError as e:
            logger.error(f"Telegram error sending invoice to user {user_id}: {e}")
            return PaymentResult(
                success=False,
                message="❌ Payment system temporarily unavailable. Please try again later."
            )
        except Exception as e:
            logger.error(f"Error handling package selection for user {user_id}: {e}")
            return PaymentResult(
                success=False,
                message="❌ Payment processing error. Please try again."
            )
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle pre-checkout query (payment verification before processing)
        """
        try:
            query = update.pre_checkout_query
            user_id = query.from_user.id
            payload = query.invoice_payload
            
            logger.info(f"Pre-checkout query from user {user_id}, payload: {payload}")
            
            # Validate payload format
            if not payload.startswith("fcb_tokens_"):
                await query.answer(ok=False, error_message="Invalid payment data")
                return False
            
            # Extract package info from payload
            try:
                parts = payload.split("_")
                package_key = parts[2]
                payment_user_id = int(parts[3])
                
                # Verify user ID matches
                if payment_user_id != user_id:
                    await query.answer(ok=False, error_message="Payment verification failed")
                    return False
                
                # Verify package exists
                if package_key not in FCB_STAR_PACKAGES:
                    await query.answer(ok=False, error_message="Invalid package")
                    return False
                
            except (IndexError, ValueError) as e:
                logger.error(f"Invalid payload format: {payload}, error: {e}")
                await query.answer(ok=False, error_message="Invalid payment data")
                return False
            
            # Approve the payment
            await query.answer(ok=True)
            logger.info(f"Pre-checkout approved for user {user_id}, package: {package_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error in pre-checkout query: {e}")
            await query.answer(ok=False, error_message="Payment verification error")
            return False
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
        """
        Handle successful payment and deliver FCB tokens
        """
        try:
            payment = update.message.successful_payment
            user_id = update.message.from_user.id
            payload = payment.invoice_payload
            
            logger.info(f"Successful payment from user {user_id}, payload: {payload}")
            
            # Extract package info from payload
            try:
                parts = payload.split("_")
                package_key = parts[2]
                payment_user_id = int(parts[3])
                
                if payment_user_id != user_id:
                    raise ValueError("User ID mismatch")
                
                if package_key not in FCB_STAR_PACKAGES:
                    raise ValueError("Invalid package")
                
                package_info = FCB_STAR_PACKAGES[package_key]
                
            except (IndexError, ValueError) as e:
                logger.error(f"Invalid successful payment payload: {payload}, error: {e}")
                return PaymentResult(
                    success=False,
                    message=PAYMENT_MESSAGES['invalid']
                )
            
            # Deliver tokens to user
            tokens_amount = package_info['tokens']
            stars_amount = package_info['stars']
            
            # Add tokens to user balance
            success, new_balance = add_fcb_tokens(
                user_id, 
                tokens_amount, 
                f"Purchase: {package_key} ({stars_amount} stars)"
            )
            
            if not success:
                logger.error(f"Failed to add tokens to user {user_id} after successful payment")
                return PaymentResult(
                    success=False,
                    message="❌ Token delivery failed. Please contact support with payment ID: " + payment.telegram_payment_charge_id
                )
            
            # Record the purchase
            record_success = record_purchase(user_id, package_key, stars_amount, tokens_amount)
            
            if not record_success:
                logger.error(f"Failed to record purchase for user {user_id}")
                # Tokens were still delivered, so this is not a critical failure
            
            # Update user activity
            update_user_activity(user_id)
            
            # Clean up pending payment
            if user_id in self.pending_payments:
                del self.pending_payments[user_id]
            
            # Get updated balance info
            balance_info = get_user_balance_info(user_id)
            
            # Create success message
            success_message = PAYMENT_MESSAGES['success'].format(
                tokens=tokens_amount,
                total_scans=balance_info['total_scans']
            )
            
            logger.info(f"Payment processed successfully - User {user_id}: +{tokens_amount} tokens (balance: {new_balance})")
            
            return PaymentResult(
                success=True,
                message=success_message,
                tokens_added=tokens_amount,
                new_balance=new_balance,
                package_info=package_info
            )
            
        except Exception as e:
            logger.error(f"Error processing successful payment: {e}")
            return PaymentResult(
                success=False,
                message="❌ Payment processing error. Please contact support."
            )
    
    def get_stars_info_message(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create informational message about Telegram Stars
        """
        info_text = """⭐ **About Telegram Stars**

🌟 **What are Telegram Stars?**
Telegram Stars are Telegram's digital currency for in-app purchases. They're secure, fast, and integrated directly into Telegram.

💳 **How to get Stars:**
• Buy them in any Telegram app
• Go to Settings → Telegram Stars
• Available payment methods vary by region

🔒 **Security:**
• Payments processed by Telegram
• No credit card info shared with bots
• Instant delivery after payment

💡 **Why Stars for FCB?**
• Fastest payment method
• Most secure option
• Available worldwide
• No external payment processors

🤖 **How it works:**
1. Select your FCB token package
2. Pay with Telegram Stars
3. Tokens delivered instantly
4. Start premium scanning immediately!

Ready to power up your crypto scanning? 🚀"""

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Store", callback_data="show_buy_menu"),
            InlineKeyboardButton("❌ Close", callback_data="close_menu")
        ]])
        
        return info_text, keyboard
    
    async def handle_payment_callback(self, user_id: int, callback_data: str,
                                    update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
        """
        Handle payment-related callback queries
        """
        try:
            if callback_data.startswith("buy_"):
                # Package selection
                package_key = callback_data.replace("buy_", "")
                return await self.handle_package_selection(user_id, package_key, update, context)
            
            elif callback_data == "stars_info":
                # Show Stars information
                info_text, keyboard = self.get_stars_info_message()
                
                await update.callback_query.edit_message_text(
                    text=info_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                return PaymentResult(success=True, message="Stars info displayed")
            
            elif callback_data == "show_buy_menu":
                # Show purchase menu
                menu_text, keyboard = self.create_purchase_menu(user_id)
                
                await update.callback_query.edit_message_text(
                    text=menu_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                return PaymentResult(success=True, message="Purchase menu displayed")
            
            elif callback_data == "close_menu":
                # Close the menu
                await update.callback_query.edit_message_text(
                    text="💰 FCB Token Store closed.\n\nUse /buy anytime to purchase more scans!"
                )
                
                return PaymentResult(success=True, message="Menu closed")
            
            elif callback_data == "retry_buy":
                # Retry purchase menu
                return await self.handle_payment_callback(user_id, "show_buy_menu", update, context)
            
            else:
                return PaymentResult(
                    success=False,
                    message="❌ Unknown payment action"
                )
                
        except Exception as e:
            logger.error(f"Error handling payment callback {callback_data} for user {user_id}: {e}")
            return PaymentResult(
                success=False,
                message="❌ Payment processing error"
            )
    
    def cleanup_expired_payments(self):
        """
        Clean up expired pending payments (older than 30 minutes)
        """
        current_time = time.time()
        expired_users = []
        
        for user_id, payment_info in self.pending_payments.items():
            if current_time - payment_info['timestamp'] > 1800:  # 30 minutes
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.pending_payments[user_id]
            logger.info(f"Cleaned up expired payment for user {user_id}")
        
        return len(expired_users)
    
    def get_payment_statistics(self) -> Dict[str, Any]:
        """
        Get payment system statistics
        """
        return {
            'pending_payments': len(self.pending_payments),
            'available_packages': len(FCB_STAR_PACKAGES),
            'system_status': 'operational'
        }

# =============================================================================
# GLOBAL PAYMENT HANDLER INSTANCE
# =============================================================================

payment_handler = FCBPaymentHandler()

# =============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# =============================================================================

def create_purchase_menu(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Create purchase menu for user"""
    return payment_handler.create_purchase_menu(user_id)

async def handle_package_selection(user_id: int, package_key: str,
                                 update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
    """Handle user selecting a token package"""
    return await payment_handler.handle_package_selection(user_id, package_key, update, context)

async def handle_pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle payment pre-checkout verification"""
    return await payment_handler.handle_pre_checkout_query(update, context)

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
    """Handle successful payment and token delivery"""
    return await payment_handler.handle_successful_payment(update, context)

async def process_payment_callback(user_id: int, callback_data: str,
                                 update: Update, context: ContextTypes.DEFAULT_TYPE) -> PaymentResult:
    """Process payment-related callback queries"""
    return await payment_handler.handle_payment_callback(user_id, callback_data, update, context)

def get_stars_info() -> Tuple[str, InlineKeyboardMarkup]:
    """Get Telegram Stars information"""
    return payment_handler.get_stars_info_message()

def cleanup_expired_payments():
    """Clean up expired pending payments"""
    return payment_handler.cleanup_expired_payments()

def get_payment_stats() -> Dict[str, Any]:
    """Get payment system statistics"""
    return payment_handler.get_payment_statistics()

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_payment_system():
    """Initialize the payment system"""
    logger.info("💳 FCB v2 Payment System initialized")
    logger.info(f"📦 Available packages: {len(FCB_STAR_PACKAGES)}")
    logger.info("⭐ Telegram Stars integration ready")
    logger.info("🔒 Secure payment processing enabled")

# Auto-initialize when module is imported
initialize_payment_system()