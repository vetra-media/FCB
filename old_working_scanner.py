"""
Scanner module for CFB (Crypto FOMO Bot) - UPDATED FOR ULTRA-CLEAN UI
Handles market scanning, FOMO opportunity detection, and automated alerts
"""

import asyncio
import logging
import time
import csv
from datetime import datetime, timedelta
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
from formatters import format_simple_message, build_broadcast_keyboard, get_buy_coin_url  # UPDATED: Use simplified formatter
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# =============================================================================
# ALERT FREQUENCY CONTROL
# =============================================================================

# Alert frequency settings
ALERT_FREQUENCY_HOURS = 4  # Every 4 hours = 6 alerts/day
MAX_ALERTS_PER_DAY = 6
daily_alert_count = 0
last_alert_date = None
alerted_coins_today = set()  # Prevent duplicate alerts same day

# =============================================================================
# USER NOTIFICATION SYSTEM (UNCHANGED)
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
    """Send FOMO alert directly to subscribed users - UPDATED FOR SIMPLIFIED UI"""
    if not subscribed_users:
        logging.info("No subscribed users for notifications")
        return
        
    # Format the message using simplified formatter
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
    
    # UPDATED: Use simplified message format for notifications
    msg = format_simple_message(
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
            # UPDATED: Send clean notification with buttons
            await bot.send_message(
                chat_id=user_id,
                text=msg,  # Use the formatted message you created
                parse_mode='HTML',
                reply_markup=keyboard  # Use the keyboard you created
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
# FOMO ANALYSIS FUNCTIONS (UNCHANGED)
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

async def calculate_fomo_status_cg_predictive(coin):
    """Enhanced scanner with predictive elements"""
    
    # Convert CoinGecko format to standard format
    coin_data = {
        'id': coin.get('id', ''),
        'symbol': coin.get('symbol', ''),
        'name': coin.get('name', ''),
        'price': coin.get('current_price', 0),
        'volume': coin.get('total_volume', 0),
        'market_cap': coin.get('market_cap', 0),
        'market_cap_rank': coin.get('market_cap_rank', 999999),
        'change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
        'change_24h': coin.get('price_change_percentage_24h_in_currency', 0)
    }
    
    # Use enhanced algorithm (returns tuple not dict)
    from analysis import calculate_fomo_status_ultra_fast_enhanced
    result = await calculate_fomo_status_ultra_fast_enhanced(coin_data)
    
    # Unpack the tuple result
    fomo_score, signal_type, trend_status, distribution_status, volume_spike = result
    
    # Return in scanner format
    return {
        "coin": coin.get('id', ''),
        "symbol": coin.get('symbol', ''),
        "name": coin.get('name', ''),
        "current_price": coin.get('current_price') or 0,
        "price_1h_change (%)": round(coin_data['change_1h'], 2),
        "price_24h_change (%)": round(coin_data['change_24h'], 2),
        "volume_24h": round(coin_data['volume'], 2),
        "volume_spike": round(volume_spike, 2),
        "fomo_score": fomo_score,
        "signal_type": signal_type,
        "logo": coin.get('image'),
        "source_url": f'https://www.coingecko.com/en/coins/{coin.get("id", "")}'
    }

# =============================================================================
# FOMO SCANNING FUNCTIONS - OPTIMIZED FOR PRO API (UNCHANGED)
# =============================================================================

async def find_top_fomo_coin():
    """Scan for top FOMO opportunities - Only return coins with 80%+ FOMO score"""
    logging.info("Starting FOMO scan (80%+ threshold)...")
    
    # Get exclusion list
    top_symbols_data = await fetch_market_data_ultra_fast(page=1, per_page=TOP_N_TO_EXCLUDE)
    top_symbols = set(t['symbol'].lower() for t in top_symbols_data)
    excluded_symbols = STABLECOIN_SYMBOLS | top_symbols

    best_coin = None
    best_score = -1
    qualifying_coins = []  # Track all coins above threshold
    page = 1
    
    while page < 8:  # Scan more pages to find 80%+ coins
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
                    
            fomo = await calculate_fomo_status_cg_predictive(coin)
            
            # NEW: Only consider coins with 80%+ FOMO score
            if fomo['fomo_score'] >= 80:
                qualifying_coins.append(fomo)
                if fomo['fomo_score'] > best_score:
                    best_coin = fomo
                    best_score = fomo['fomo_score']
                
        page += 1
        await asyncio.sleep(0.5)
        
    if best_coin:
        logging.info(f"🎯 HIGH FOMO ALERT: {best_coin['symbol']} with score {best_coin['fomo_score']}% - {best_coin['signal_type']}")
        logging.info(f"📊 Found {len(qualifying_coins)} coins above 80% threshold")
    else:
        logging.info("❌ No coins found above 80% FOMO threshold")
        
    return best_coin

# =============================================================================
# BROADCASTING AND ALERTS - UPDATED FOR ULTRA-CLEAN UI
# =============================================================================

# =============================================================================
# WEEKLY WINNERS TRACKING
# =============================================================================

async def log_alert_for_winners_tracking(coin_data):
    """Log alert for weekly winners tracking"""
    try:
        # Enhanced CSV logging with timestamp for winners tracking
        fieldnames = [
            "date", "timestamp", "name", "symbol", "coin", "current_price",
            "price_1h_change (%)", "price_24h_change (%)",
            "volume_24h", "volume_spike", "fomo_score", "signal_type"
        ]
        
        file_exists = Path(HISTORY_LOG).exists()
        with open(HISTORY_LOG, "a", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            now = datetime.now()
            coinrow = {
                **coin_data, 
                "date": now.isoformat(),
                "timestamp": int(now.timestamp())  # For easy date calculations
            }
            writer.writerow({k: coinrow.get(k, "") for k in fieldnames})
            
        logging.info(f"📝 Logged alert for winners tracking: {coin_data['symbol']}")
        
    except Exception as e:
        logging.error(f"Error logging alert for winners tracking: {e}")

async def get_weekly_winners():
    """Get coins that were alerted in past 7 days and are now up"""
    try:
        if not Path(HISTORY_LOG).exists():
            return []
        
        # Get current prices for comparison
        from api_client import get_coin_info_ultra_fast
        
        winners = []
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Read recent alerts from CSV
        with open(HISTORY_LOG, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    alert_date = datetime.fromisoformat(row['date'])
                    if alert_date >= seven_days_ago:
                        
                        # Get current price
                        coin_id = row['coin']
                        _, current_coin_data = await get_coin_info_ultra_fast(coin_id)
                        
                        if current_coin_data:
                            alert_price = float(row['current_price'])
                            current_price = float(current_coin_data.get('price', 0))
                            
                            if current_price > alert_price:
                                gain_percent = ((current_price - alert_price) / alert_price) * 100
                                days_ago = (datetime.now() - alert_date).days
                                
                                winners.append({
                                    'name': row['name'],
                                    'symbol': row['symbol'],
                                    'coin_id': coin_id,
                                    'alert_price': alert_price,
                                    'current_price': current_price,
                                    'gain_percent': gain_percent,
                                    'days_ago': days_ago,
                                    'alert_date': alert_date
                                })
                                
                except Exception as e:
                    logging.debug(f"Error processing row for winners: {e}")
                    continue
        
        # Sort by gain percentage (highest first)
        winners.sort(key=lambda x: x['gain_percent'], reverse=True)
        return winners[:10]  # Top 10 winners
        
    except Exception as e:
        logging.error(f"Error getting weekly winners: {e}")
        return []

async def send_weekly_winners_update(bot):
    """Send daily update of previous week's winners"""
    try:
        winners = await get_weekly_winners()
        
        if not winners:
            logging.info("📊 No weekly winners to report")
            return
        
        # Build winners message
        msg = "🏆 <b>Weekly Winners Update</b>\n\n"
        msg += "Coins we alerted in the past 7 days that are UP:\n\n"
        
        for i, winner in enumerate(winners[:5], 1):  # Top 5 winners
            msg += f"💚 <b>{winner['name']}</b> ({winner['symbol']})\n"
            msg += f"   🎯 Alert: {winner['days_ago']} days ago\n"
            msg += f"   📈 Gain: <b>+{winner['gain_percent']:.1f}%</b>\n\n"
        
        msg += "🎯 <i>Great picks! Keep watching for more opportunities.</i>\n"
        msg += f"📊 <i>Found {len(winners)} winners out of recent alerts</i>"
        
        # Send to all subscribed users
        success_count = 0
        for user_id in subscribed_users.copy():
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=msg,
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                error_msg = str(e).lower()
                if "forbidden" in error_msg or "chat not found" in error_msg:
                    subscribed_users.discard(user_id)
                    save_subscriptions()
                    logging.warning(f"Removed inactive user {user_id} from winners update")
                else:
                    logging.error(f"Error sending winners update to {user_id}: {e}")
        
        logging.info(f"✅ Weekly winners update sent to {success_count} users")
        
    except Exception as e:
        logging.error(f"Error sending weekly winners update: {e}")

async def periodic_fomo_scan(bot):
    """Run periodic FOMO scans with daily limits and 80%+ threshold"""
    global daily_alert_count, last_alert_date, alerted_coins_today
    
    logging.info("⏳ Waiting 7 seconds before first FOMO scan...")
    await asyncio.sleep(7)
    
    while True:
        try:
            # Reset daily counter at midnight
            current_date = datetime.now().date()
            if last_alert_date != current_date:
                daily_alert_count = 0
                last_alert_date = current_date
                alerted_coins_today = set()
                logging.info(f"📅 New day: Reset alert counter (Max: {MAX_ALERTS_PER_DAY}/day)")
            
            # Check daily limit
            if daily_alert_count >= MAX_ALERTS_PER_DAY:
                logging.info(f"📊 Daily alert limit reached ({daily_alert_count}/{MAX_ALERTS_PER_DAY})")
                # Wait until next scan time
                next_scan_time = ALERT_FREQUENCY_HOURS * 3600  # Still check every 4 hours
                logging.info(f"Next scan in {ALERT_FREQUENCY_HOURS} hours...")
                await asyncio.sleep(next_scan_time)
                continue
            
            logging.info(f"Starting FOMO scan ({daily_alert_count}/{MAX_ALERTS_PER_DAY} alerts sent today)...")
            
            # Find top opportunity (80%+ threshold)
            top_coin = await find_top_fomo_coin()
            
            if top_coin:
                coin_symbol = top_coin['symbol']
                
                # Check if we already alerted this coin today
                if coin_symbol in alerted_coins_today:
                    logging.info(f"⏭️ Skipping {coin_symbol} - already alerted today")
                else:
                    # Send to subscribed users only (no channel broadcast)
                    await send_notification_to_users(bot, top_coin)
                    
                    # Track this alert
                    daily_alert_count += 1
                    alerted_coins_today.add(coin_symbol)
                    
                    # Log the pick for weekly winners tracking
                    await log_alert_for_winners_tracking(top_coin)
                    
                    logging.info(f"✅ Alert sent: {coin_symbol} ({daily_alert_count}/{MAX_ALERTS_PER_DAY} today)")
            else:
                logging.info("❌ No coins above 80% threshold found")
            
            # Wait for next scan (4 hours)
            next_scan_hours = ALERT_FREQUENCY_HOURS
            logging.info(f"Next FOMO scan in {next_scan_hours} hours...")
            await asyncio.sleep(next_scan_hours * 3600)
            
        except Exception as e:
            logging.error(f"Error in periodic FOMO scan: {e}")
            # Wait 30 minutes before retrying on error
            await asyncio.sleep(1800)