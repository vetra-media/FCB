import random
import logging

# === SIGNAL REWARDS CONFIGURATION (Simplified: fixed 1–3 token reward, same chance for all coins) ===
TIERS = []  # No tiers needed for simplified version

DEFAULT_POOL_SIZE = 200  # Wrapped config value to allow flexible pool size

def build_signal_rewards_lookup(coin_list, user_win_history=None):
    """
    Assigns default values for all coins — every coin gets equal chance.
    Filters out coins already seen in user's session.
    """
    lookup = {
        "tier_lookup": {},
        "probability_lookup": {},
        "token_range_lookup": {},
        "win_messages": {},
    }

    seen = set(user_win_history) if isinstance(user_win_history, (list, set)) else set()
    filtered_list = [coin for coin in coin_list if (coin.get('id') or coin.get('symbol', '')).lower().strip() not in seen]

    trimmed_list = filtered_list[:DEFAULT_POOL_SIZE] or coin_list[:DEFAULT_POOL_SIZE]  # fallback if all were seen

    for coin in trimmed_list:
        coin_id = (coin.get('id') or coin.get('symbol', 'unknown-symbol')).lower().strip()
        if not coin_id:
            logging.warning(f"⚠️ Skipping coin with no valid ID or symbol: {coin}")
            continue

        # Equal treatment for all coins
        lookup["tier_lookup"][coin_id] = "Standard"
        lookup["probability_lookup"][coin_id] = 0.35  # ~1 in 2.85 chance
        lookup["token_range_lookup"][coin_id] = (1, 3)
        lookup["win_messages"][coin_id] = "🎉 Lucky scan! You've earned a reward."

    logging.debug(f"✅ Built signal rewards for {len(lookup['probability_lookup'])} coins")
    logging.debug(f"🔍 Sample coin IDs: {list(lookup['probability_lookup'].keys())[:5]}")

    return lookup

def normalise_coin_input(user_input, coin_list):
    """
    Matches user input (name, ID, or symbol) to a valid coin ID.
    Returns the ID or symbol that matches what the lookup expects.
    """
    user_input = user_input.lower().strip()
    for coin in coin_list:
        for key in ("id", "symbol", "name"):
            if coin.get(key, "").lower().strip() == user_input:
                return (coin.get("id") or coin.get("symbol")).lower().strip()
    return None

def evaluate_scan_reward(fomo_score, coin_id=None, lookup=None, user_win_history=None):
    """
    Each scan has a flat chance to win 1–3 tokens, unless it's a duplicate coin in the session.
    """
    if lookup is None:
        return False, 0, "Unknown"

    coin_id = (coin_id or '').lower().strip()
    logging.debug(f"🔎 Evaluating coin_id: {coin_id}")

    if isinstance(user_win_history, (list, set)) and coin_id in user_win_history:
        logging.debug(f"⛔ Duplicate scan for {coin_id} — no reward or charge applied")
        return False, 0, "Duplicate"

    tier = lookup["tier_lookup"].get(coin_id, "Standard")
    win_chance = lookup["probability_lookup"].get(coin_id, 0.35)
    reward_range = lookup["token_range_lookup"].get(coin_id, (1, 3))

    random_chance = random.random()
    logging.debug(f"🎯 SCAN → Coin ID: {coin_id}, Chance: {win_chance:.2f}, Rand: {random_chance:.2f}")

    if random_chance < win_chance:
        tokens_awarded = random.randint(*reward_range)
        logging.debug(f"🏆 WIN! {tokens_awarded} tokens awarded")
    else:
        tokens_awarded = 0
        logging.debug("🙁 No reward this time")

    is_visual_winner = tokens_awarded > 0
    return is_visual_winner, tokens_awarded, tier

# === SAFETY WRAPPERS (fallback stubs to satisfy imports) ===
def periodic_fomo_scan(*args, **kwargs):
    logging.info("🔧 Stub: periodic_fomo_scan() called with args")

def send_weekly_winners_update(*args, **kwargs):
    logging.info("🔧 Stub: send_weekly_winners_update() called with args")

def add_user_to_notifications(user_id):
    logging.info(f"🔧 Stub: add_user_to_notifications({user_id}) called")

subscribed_users = set()

def save_subscriptions():
    logging.info("🔧 Stub: save_subscriptions() called (not implemented)")
