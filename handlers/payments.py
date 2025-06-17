"""
handlers/payments.py - Payment Processing
Telegram Stars payment handling with proper validation
"""

import logging

from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes

# Core imports
from .core import safe_edit_message, get_db_connection

from config import FCB_STAR_PACKAGES
from database import add_fcb_tokens

# =============================================================================
# Payment Handlers - Complete Stars Payment Processing
# =============================================================================

async def handle_star_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle star purchase button clicks with clean error handling"""
    query = update.callback_query
    
    package_key = query.data.replace("buy_", "")
    if package_key in FCB_STAR_PACKAGES:
        package = FCB_STAR_PACKAGES[package_key]
        
        try:
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=package['title'],
                description=package['description'],
                payload=f"fcb_{package_key}_{query.from_user.id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(package['title'], package['stars'])],
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False
            )
        except Exception as e:
            logging.error(f"Error sending invoice: {e}")
            await safe_edit_message(query, text="❌ Error creating invoice. Please try again.")

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout validation for payment security"""
    query = update.pre_checkout_query
    
    if query.invoice_payload.startswith("fcb_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid purchase")

async def payment_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful Stars payments with accurate economics messaging"""
    payment = update.message.successful_payment
    actual_buyer_id = update.effective_user.id
    
    logging.info(f"🔍 PAYMENT DEBUG: Buyer ID: {actual_buyer_id}")
    logging.info(f"🔍 PAYMENT DEBUG: Payload: {payment.invoice_payload}")
    logging.info(f"🔍 PAYMENT DEBUG: Stars amount: {payment.total_amount}")
    
    payload_parts = payment.invoice_payload.split("_")
    
    if len(payload_parts) == 3 and payload_parts[0] == "fcb":
        package_key = payload_parts[1]
        payload_user_id = int(payload_parts[2])
        
        if actual_buyer_id != payload_user_id:
            logging.error(f"❌ SECURITY ALERT: Buyer {actual_buyer_id} != Payload {payload_user_id}")
            await update.message.reply_text(
                "❌ Payment verification failed. Please contact support.",
                parse_mode='HTML'
            )
            return
        
        if package_key in FCB_STAR_PACKAGES:
            tokens = FCB_STAR_PACKAGES[package_key]['tokens']
            stars = FCB_STAR_PACKAGES[package_key]['stars']
            
            success, new_balance = add_fcb_tokens(actual_buyer_id, tokens)
            
            if success:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE users 
                            SET first_purchase_date = CURRENT_TIMESTAMP 
                            WHERE user_id = ? AND first_purchase_date IS NULL
                        ''', (actual_buyer_id,))
                        conn.commit()
                except Exception as e:
                    logging.error(f"Error updating first purchase date: {e}")
                
                # Enhanced success message with accurate economics explanation
                message = f"""🎉 <b>Purchase Successful!</b>

💎 <b>{tokens} FCB tokens</b> added to your account!
⭐ <b>{stars} Stars</b> spent

📊 <b>Your Balance:</b>
💎 FCB Tokens: <b>{new_balance}</b>
🎯 Premium Scans: <b>{tokens} available!</b>

💰 <b>What You Can Do:</b>
🟢 <b>Always FREE:</b> ⬅️ BACK navigation, 💰 buy links
🔴 <b>1 token each:</b> New coin searches, 👉 NEXT discoveries

🔥 <b>Alert Benefits:</b>
✅ Keep receiving premium alerts (FREE)
🎯 Navigate freely from any alert
⚡ Smart token usage with cached history

🚀 <b>Ready to scan?</b> Type any coin name to get started!

💡 <b>Pro Tip:</b> Use alerts and BACK navigation to explore more without spending tokens!"""
                
                await update.message.reply_text(message, parse_mode='HTML')
                
                logging.info(f"✅ PAYMENT SUCCESS: User {actual_buyer_id} bought {tokens} FCB tokens for {stars} Stars - New balance: {new_balance}")
            else:
                logging.error(f"❌ PAYMENT FAILED: Database error for user {actual_buyer_id}")
                await update.message.reply_text(
                    "❌ Payment processed but token delivery failed. Please contact support with this transaction ID.",
                    parse_mode='HTML'
                )
        else:
            logging.error(f"❌ Invalid package key: {package_key}")
            await update.message.reply_text(
                "❌ Invalid purchase package. Please contact support.",
                parse_mode='HTML'
            )
    else:
        logging.error(f"❌ Invalid payment payload: {payment.invoice_payload}")
        await update.message.reply_text(
            "❌ Payment verification failed. Please contact support.",
            parse_mode='HTML'
        )