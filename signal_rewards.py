import random
import logging

# === SIGNAL REWARDS CONFIGURATION (Signal-Based Tiering, Clean UX) ===
TIERS = [
    {"name": "Jackpot", "count": 1, "payout": (50, 100), "base_prob": 0.01},
    {"name": "Diamond", "count": 4, "payout": (25, 60),  "base_prob": 0.03},
    {"name": "Gold",    "count": 10, "payout": (10, 30), "base_prob": 0.09},
    {"name": "Silver",  "count": 25, "payout": (5, 15),  "base_prob": 0.18},
    {"name": "Bronze",  "count": 60, "payout": (2, 6),   "base_prob": 0.24},
]

def build_signal_rewards_lookup(coin_list):
    """
    Takes a list of coins sorted by FOMO (highest first) and assigns them to tier buckets.
    Returns a complete SIGNAL_REWARDS_LOOKUP dict.
    """
    lookup = {
        "tier_lookup": {},
        "probability_lookup": {},
        "token_range_lookup": {},
        "win_messages": {},
    }

    idx = 0
    for tier in TIERS:
        for _ in range(tier["count"]):
            if idx >= len(coin_list):
                break

            coin = coin_list[idx]
            coin_id = coin.get('id')
            if not coin_id:
                idx += 1
                continue

            fomo = coin.get("fomo_score", 50)

            # Assign tier
            lookup["tier_lookup"][coin_id] = tier["name"]
            lookup["probability_lookup"][coin_id] = tier["base_prob"] * (fomo / 100)
            lookup["token_range_lookup"][coin_id] = tier["payout"]
            lookup["win_messages"][coin_id] = f"Signal match: {tier['name']} tier"
            idx += 1

    return lookup

def evaluate_scan_reward(fomo_score, coin_id=None, lookup=None):
    """
    Determines if the scan results in a token reward based on the coin’s FOMO score and tier.
    Returns:
        (bool is_visual_winner, int tokens_awarded, str tier_label)
    """
    if lookup is None:
        return False, 0, "Unknown"

    tier = lookup["tier_lookup"].get(coin_id, "Bronze")
    base_chance = lookup["probability_lookup"].get(coin_id, 0.01)
    reward_range = lookup["token_range_lookup"].get(coin_id, (3, 7))

    win_chance = base_chance
    random_chance = random.random()

    logging.debug(f"🔍 REWARD LOOKUP MATCH: coin_id={coin_id} found={coin_id in lookup['tier_lookup']}")
    logging.debug(f"🎯 REWARD DEBUG → Coin ID: {coin_id}, Tier: {tier}, FOMO: {fomo_score}, Chance: {win_chance:.3f}, Rand: {random_chance:.3f}")

    if random_chance < win_chance:
        tokens_awarded = random.randint(*reward_range)
    elif fomo_score >= 70:
        tokens_awarded = random.choice([1, 2])  # fallback for strong signals
    else:
        tokens_awarded = 0

    is_visual_winner = tokens_awarded > 0
    return is_visual_winner, tokens_awarded, tier
