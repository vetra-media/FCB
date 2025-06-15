"""
Scanner module for CFB (Crypto FOMO Bot)
Handles market scanning, FOMO opportunity detection, and automated alerts
"""

import asyncio
import logging
import time
import csv
from datetime import datetime
from pathlib import Path
from io import BytesIO
import requests
import pickle 

from config import (
    STABLECOIN_SYMBOLS, TOP_N_TO_EXCLUDE, MAX_COINS_PER_PAGE,
    FOMO_SCAN_INTERVAL, HISTORY_LOG, BROADCAST_CHAT_ID
)
from api_client import fetch_market_data_ultra_fast, batch_processor
from analysis import calculate_fomo_status_ultra_fast, analyze_momentum_trend, analyze_exchange_distribution, calculate_real_volume_spike
from formatters import format_fomo_message, build_broadcast_keyboard, get_buy_coin_url
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# =============================================================================
# USER NOTIFICATION SYSTEM
# =============================================================================

# Persistent subscription storage
SUBSCRIPTIONS_FILE = Path("subscriptions.pkl")

def load_subscriptions():
    """Load subscriptions from file"""
    try:
        if SUBSCRIPTIONS_FILE.exists():
            with open(SUBSCRIPTIONS_FILE, 'rb') as f:
                loaded_users = pickle.load(f)
                logging.info(f"Successfully loaded {len(loaded_users)} subscribers from {SUBSCRIPTIONS_FILE}")
                return loaded_users
        else:
            logging.info(f"No subscription file found at {SUBSCRIPTIONS_FILE}")
    except Exception as e:
        logging.error(f"Failed to load subscriptions: {e}")
    return set()

def save_subscriptions():
    """Save subscriptions to file"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'wb') as f:
            pickle.dump(subscribed_users, f)
    except Exception as e:
        logging.error(f"Failed to save subscriptions: {e}")

subscribed_users = load_subscriptions()  # Load existing subscriptions
logging.info(f"Loaded {len(subscribed_users)} existing subscribers from file")

def add_user_to_notifications(user_id):
    """Add user to notification list"""
    subscribed_users.add(user_id)
    save_subscriptions()  # Save to file
    logging.info(f"User {user_id} subscribed to notifications")

async def send_notification_to_users(bot, coin_data):
    """Send FOMO alert directly to subscribed users"""
    if not subscribed_users:
        logging.info("No subscribed users for notifications")
        return
        
    # Format the message (same as broadcast but for private chat)
    coin_info = {
        'id': coin_data['coin'],
        'name': coin_data['name'],
        'symbol': coin_data['symbol'],
        'price': coin_data['current_price'],
        'change_1h': coin_data['price_1h_change (%)'],
        'change_24h': coin_data['price_24h_change (%)'],
        'volume': coin_data['volume_24h'],
        'source_url': coin_data['source_url'],
        'logo': coin_data.get('logo')
    }
    
    msg = format_fomo_message(
        coin_info, 
        coin_data['fomo_score'], 
        coin_data['signal_type'], 
        coin_data['volume_spike'],
        "Analyzing...",  # trend_status 
        "Analyzing...",  # distribution_status
        is_broadcast=False  # This makes it show coin name properly
    )
    
    # Add interactive buttons (these work in private chats!)
    from formatters import build_addictive_buttons
    keyboard = build_addictive_buttons(coin_info)
    
# Send to all subscribed users
    for user_id in subscribed_users.copy():  # Use copy() to avoid modification during iteration
        try:
            # Send short notification that brings them back to bot
            await bot.send_message(
                chat_id=user_id,
                text=f"🚨 <b>FOMO Alert!</b> {coin_info['symbol']} showing strong signals. Click to analyze! 🎯",
                parse_mode='HTML'
            )
            logging.info(f"Notification sent to user {user_id}")
        except Exception as e:
            error_msg = str(e).lower()
            if "forbidden" in error_msg:
                # User blocked the bot
                logging.warning(f"🚫 User {user_id} blocked bot - removing from notifications")
                subscribed_users.discard(user_id)
                save_subscriptions()
            elif "chat not found" in error_msg:
                # Chat doesn't exist anymore
                logging.warning(f"❌ Chat not found for user {user_id} - removing from notifications")
                subscribed_users.discard(user_id)
                save_subscriptions()
            elif "timed out" in error_msg:
                # Just log timeout, don't remove user
                logging.warning(f"⏰ Timeout sending to user {user_id} - will retry later")
            else:
                logging.error(f"❌ Unexpected error sending to user {user_id}: {e}")

# =============================================================================
# FOMO ANALYSIS FUNCTIONS
# =============================================================================

def calculate_basic_fomo_score(coin, volume_spike):
    """Fast FOMO calculation without heavy API calls"""
    price_1h_change = coin.get('change_1h', 0) or 0
    price_24h_change = coin.get('change_24h', 0) or 0
    current_volume = coin.get('volume', 0) or 0
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    fomo_score = 0
    
    # Base score from volume spike (0-60 points)
    if volume_spike >= 10.0:
        fomo_score = 60
    elif volume_spike >= 5.0:
        fomo_score = 45 + int((volume_spike - 5.0) * 3)
    elif volume_spike >= 2.5:
        fomo_score = 30 + int((volume_spike - 2.5) * 6)
    elif volume_spike >= 1.5:
        fomo_score = 15 + int((volume_spike - 1.5) * 15)
    else:
        fomo_score = int(volume_spike * 10)
    
    # Quick price movement modifiers
    abs_24h_change = abs(price_24h_change)
    
    if abs_24h_change < 2.0 and volume_spike >= 3.0:
        fomo_score += 25
    elif abs_24h_change < 5.0 and volume_spike >= 2.0:
        fomo_score += 15
    elif 5.0 <= abs_24h_change <= 15.0:
        fomo_score += 10
    elif abs_24h_change > 25.0:
        fomo_score -= 15
    
    # 1-hour momentum bonus/penalty
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    
    # Volume size bonus/penalty
    if current_volume > 10_000_000:
        fomo_score += 5
    elif current_volume > 1_000_000:
        fomo_score += 1
    elif current_volume < 100_000:
        fomo_score -= 20
    
    return max(0, min(100, fomo_score))

def determine_signal_type(fomo_score, abs_24h_change):
    """Quick signal type determination"""
    if fomo_score >= 85 and abs_24h_change < 5.0:
        return "🎯 Stealth Accumulation"
    elif fomo_score >= 75:
        return "⚡ Early Momentum"
    elif fomo_score >= 60:
        return "🟡 Volume Building"
    elif fomo_score >= 40 and abs_24h_change > 20.0:
        return "🚨 Already Pumping"
    elif fomo_score >= 35:
        return "📈 Moderate Activity"
    elif fomo_score >= 20:
        return "👀 Watch List"
    else:
        return "😴 Low Activity"

def calculate_real_volume_spike_from_coin(coin):
    """Calculate volume spike for FOMO scanning"""
    coin_id = coin.get('id', '')
    current_volume = coin.get('total_volume', 0)
    return calculate_real_volume_spike(coin_id, current_volume)

def calculate_fomo_status_cg(coin):
    """Calculate FOMO status for market scanning"""
    price_1h_change = coin.get('price_change_percentage_1h_in_currency') or 0
    price_24h_change = coin.get('price_change_percentage_24h_in_currency') or 0
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    volume_spike = calculate_real_volume_spike_from_coin(coin)
    current_volume = coin.get('total_volume', 0)
    
    fomo_score = 0
    signal_type = "No Signal"
    
    # Base score from volume spike (0-60 points)
    if volume_spike >= 10.0:
        fomo_score = 60
    elif volume_spike >= 5.0:
        fomo_score = 45 + int((volume_spike - 5.0) * 3)
    elif volume_spike >= 2.5:
        fomo_score = 30 + int((volume_spike - 2.5) * 6)
    elif volume_spike >= 1.5:
        fomo_score = 15 + int((volume_spike - 1.5) * 15)
    else:
        fomo_score = int(volume_spike * 10)
    
    # Price movement modifiers
    abs_24h_change = abs(price_24h_change)
    
    if abs_24h_change < 2.0 and volume_spike >= 3.0:
        fomo_score += 25
    elif abs_24h_change < 5.0 and volume_spike >= 2.0:
        fomo_score += 15
    elif 5.0 <= abs_24h_change <= 15.0:
        fomo_score += 10
    elif abs_24h_change > 25.0:
        fomo_score -= 15
    elif abs_24h_change > 50.0:
        fomo_score -= 25
    
    # 1-hour momentum bonus/penalty
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    elif price_1h_change < 0 and price_24h_change > 0:
        fomo_score += 1
    
    # Volume size bonus/penalty
    if current_volume > 10_000_000:
        fomo_score += 5
    elif current_volume > 5_000_000:
        fomo_score += 3
    elif current_volume > 1_000_000:
        fomo_score += 1
    elif current_volume < 100_000:
        fomo_score -= 20
    elif current_volume < 500_000:
        fomo_score -= 10
    
    # High price coin penalty
    coin_price = coin.get('current_price', 0) or 0
    try:
        coin_price = float(coin_price)
        if coin_price > 1000 and current_volume < 1_000_000:
            fomo_score -= 25
        elif coin_price > 100 and current_volume < 500_000:
            fomo_score -= 15
    except:
        pass
    
    # Ensure score stays within 0-100 range
    fomo_score = max(0, min(100, fomo_score))
    
    # Determine signal type
    signal_type = determine_signal_type(fomo_score, abs_24h_change)

    return {
        "coin": coin.get('id', ''),
        "symbol": coin.get('symbol', ''),
        "name": coin.get('name', ''),
        "current_price": coin.get('current_price') or 0,
        "price_1h_change (%)": round(price_1h_change, 2),
        "price_24h_change (%)": round(price_24h_change, 2),
        "volume_24h": round(current_volume, 2),
        "volume_spike": round(volume_spike, 2),
        "fomo_score": fomo_score,
        "signal_type": signal_type,
        "logo": coin.get('image'),
        "source_url": f'https://www.coingecko.com/en/coins/{coin.get("id", "")}'
    }

# =============================================================================
# FOMO SCANNING FUNCTIONS - OPTIMIZED FOR PRO API
# =============================================================================

async def find_top_fomo_coin():
    """Scan for top FOMO opportunities"""
    logging.info("Starting FOMO scan...")
    
    # Get exclusion list
    top_symbols_data = await fetch_market_data_ultra_fast(page=1, per_page=TOP_N_TO_EXCLUDE)
    top_symbols = set(t['symbol'].lower() for t in top_symbols_data)
    excluded_symbols = STABLECOIN_SYMBOLS | top_symbols

    best_coin = None
    best_score = -1
    page = 1
    
    while not best_coin and page < 8:
        logging.info(f"Scanning CoinGecko page {page}...")
        tickers = await fetch_market_data_ultra_fast(page=page, per_page=MAX_COINS_PER_PAGE)
        if not tickers:
            break
            
        for coin in tickers:
            symbol = coin.get('symbol', '').lower()
            if symbol in excluded_symbols:
                continue
                
            market_cap = coin.get('market_cap', 0)
            if market_cap is None:
                continue
                
            # Ensure required fields exist
            for field in ['price_change_percentage_1h_in_currency', 'price_change_percentage_24h_in_currency', 'total_volume', 'current_price']:
                if coin.get(field) is None:
                    coin[field] = 0
                    
            fomo = calculate_fomo_status_cg(coin)
            
            if fomo['fomo_score'] > best_score:  # Broadcast the best coin, regardless of score
                best_coin = fomo
                best_score = fomo['fomo_score']
                
        page += 1
        await asyncio.sleep(0.5)
        
    if best_coin:
        logging.info(f"Top FOMO coin: {best_coin['symbol']} with score {best_coin['fomo_score']} - {best_coin['signal_type']}")
    else:
        logging.info("No FOMO opportunities found in scan.")
        
    return best_coin

# =============================================================================
# BROADCASTING AND ALERTS
# =============================================================================

async def broadcast_fomo_alert(bot, coin_data):
    """Broadcast FOMO alert to channel WITH ADDICTIVE BUTTONS"""
    if not BROADCAST_CHAT_ID:
        logging.error("No broadcast chat ID configured!")
        return
        
    try:
        # Format as broadcast message
        coin_info = {
            'id': coin_data['coin'],
            'name': coin_data['name'],
            'symbol': coin_data['symbol'],
            'price': coin_data['current_price'],
            'change_1h': coin_data['price_1h_change (%)'],
            'change_24h': coin_data['price_24h_change (%)'],
            'volume': coin_data['volume_24h'],
            'source_url': coin_data['source_url'],
            'logo': coin_data.get('logo')
        }
        
        # Get trend and exchange analysis for broadcasts
        coin_id = coin_data['coin']
        current_volume = coin_data['volume_24h']
        price_1h_change = coin_data['price_1h_change (%)']
        price_24h_change = coin_data['price_24h_change (%)']
        
        # Analyze momentum trend
        trend_score, trend_status = analyze_momentum_trend(coin_id, current_volume, price_1h_change, price_24h_change)
        
        # Analyze exchange distribution  
        distribution_score, distribution_status = analyze_exchange_distribution(coin_id)
        
        msg = format_fomo_message(
            coin_info, 
            coin_data['fomo_score'], 
            coin_data['signal_type'], 
            coin_data['volume_spike'],
            trend_status,
            distribution_status,
            is_broadcast=True
        )
        
        # Create keyboard with tracking URL for BUY COIN button
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('⬅️ BACK', callback_data=f"back_{coin_data['coin']}"),
                InlineKeyboardButton('🎰 NEXT', callback_data="next_coin")
            ],
            [
                InlineKeyboardButton('💰 BUY COIN', url=get_buy_coin_url(coin_info))
            ]
        ])
        
        # Try to send with logo first
        logo_url = coin_info.get('logo')
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=6)
                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    image_bytes = BytesIO(response.content)
                    await bot.send_photo(
                        chat_id=BROADCAST_CHAT_ID,
                        photo=image_bytes,
                        caption=msg,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                    logging.info(f"Broadcast sent with photo for {coin_data['symbol']}")
                    return
            except Exception as e:
                logging.warning(f"Photo send failed: {e}")
        
        # Fallback to text message
        await bot.send_message(
            chat_id=BROADCAST_CHAT_ID,
            text=msg,
            parse_mode='HTML',
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        logging.info(f"Broadcast sent as text for {coin_data['symbol']}")
        
    except Exception as e:
        logging.error(f"Error broadcasting FOMO alert: {e}")

async def periodic_fomo_scan(bot):
    """Run periodic FOMO scans and broadcast alerts"""
    logging.info("⏳ Waiting 7 seconds before first FOMO scan...")
    await asyncio.sleep(7)
    
    while True:
        try:
            logging.info("Starting periodic FOMO scan...")
            
            # Find top opportunity
            top_coin = await find_top_fomo_coin()
            
            if top_coin:
                await broadcast_fomo_alert(bot, top_coin)
                
                # Send to subscribed users (NEW)
                await send_notification_to_users(bot, top_coin)
                
                # Log the pick
                fieldnames = [
                    "date", "name", "symbol", "coin", "current_price",
                    "price_1h_change (%)", "price_24h_change (%)",
                    "volume_24h", "volume_spike", "fomo_score", "signal_type"
                ]
                file_exists = Path(HISTORY_LOG).exists()
                with open(HISTORY_LOG, "a", newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    date_now = datetime.now().isoformat()
                    coinrow = {**top_coin, "date": date_now}
                    writer.writerow({k: coinrow.get(k, "") for k in fieldnames})
            else:
                logging.info("No FOMO opportunities found this scan.")
            
            # Wait for next scan
            logging.info(f"Next FOMO scan in {FOMO_SCAN_INTERVAL/3600:.1f} hours...")
            await asyncio.sleep(FOMO_SCAN_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in periodic FOMO scan: {e}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)

            # Add these functions to scanner.py:

def calculate_basic_fomo_score(coin, volume_spike):
    """Fast FOMO calculation without heavy API calls"""
    price_1h_change = coin.get('change_1h', 0) or 0
    price_24h_change = coin.get('change_24h', 0) or 0
    current_volume = coin.get('volume', 0) or 0
    
    try:
        price_1h_change = float(price_1h_change)
        price_24h_change = float(price_24h_change)
    except:
        price_1h_change = 0
        price_24h_change = 0
    
    fomo_score = 0
    
    # Base score from volume spike (0-60 points)
    if volume_spike >= 10.0:
        fomo_score = 60
    elif volume_spike >= 5.0:
        fomo_score = 45 + int((volume_spike - 5.0) * 3)
    elif volume_spike >= 2.5:
        fomo_score = 30 + int((volume_spike - 2.5) * 6)
    elif volume_spike >= 1.5:
        fomo_score = 15 + int((volume_spike - 1.5) * 15)
    else:
        fomo_score = int(volume_spike * 10)
    
    # Quick price movement modifiers
    abs_24h_change = abs(price_24h_change)
    
    if abs_24h_change < 2.0 and volume_spike >= 3.0:
        fomo_score += 25
    elif abs_24h_change < 5.0 and volume_spike >= 2.0:
        fomo_score += 15
    elif 5.0 <= abs_24h_change <= 15.0:
        fomo_score += 10
    elif abs_24h_change > 25.0:
        fomo_score -= 15
    
    # 1-hour momentum bonus/penalty
    if price_1h_change > 0 and price_24h_change > 0:
        fomo_score += min(10, int(price_1h_change * 2))
    elif price_1h_change < -2.0:
        fomo_score -= min(15, int(abs(price_1h_change) * 2))
    
    # Volume size bonus/penalty
    if current_volume > 10_000_000:
        fomo_score += 5
    elif current_volume > 1_000_000:
        fomo_score += 1
    elif current_volume < 100_000:
        fomo_score -= 20
    
    return max(0, min(100, fomo_score))

def determine_signal_type(fomo_score, abs_24h_change):
    """Quick signal type determination"""
    if fomo_score >= 85 and abs_24h_change < 5.0:
        return "🎯 Stealth Accumulation"
    elif fomo_score >= 75:
        return "⚡ Early Momentum"
    elif fomo_score >= 60:
        return "🟡 Volume Building"
    elif fomo_score >= 40 and abs_24h_change > 20.0:
        return "🚨 Already Pumping"
    elif fomo_score >= 35:
        return "📈 Moderate Activity"
    elif fomo_score >= 20:
        return "👀 Watch List"
    else:
        return "😴 Low Activity"