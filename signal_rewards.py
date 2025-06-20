import random
import logging

# === SIGNAL REWARDS CONFIGURATION (Simplified: fixed 1–3 token reward, same chance for all coins) ===
TIERS = []  # No tiers needed for simplified version

def build_signal_rewards_lookup(coin_list):
    """
    Assigns default values for all coins — every coin gets equal chance.
    """
    lookup = {
        "tier_lookup": {},
        "probability_lookup": {},
        "token_range_lookup": {},
        "win_messages": {},
    }

    for coin in coin_list:
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

def evaluate_scan_reward(fomo_score, coin_id=None, lookup=None, user_win_history=None):
    """
    Each scan has a flat chance to win 1–3 tokens, regardless of coin or FOMO score.
    """
    if lookup is None:
        return False, 0, "Unknown"

    coin_id = (coin_id or '').lower().strip()
    logging.debug(f"🔎 Evaluating coin_id: {coin_id}")

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
