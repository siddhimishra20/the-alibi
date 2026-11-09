"""THE ALIBI: Detective scoring and career rank progression system."""

from typing import Dict, Any, Tuple

# Rank definitions from Junior Gumshoe to Legendary Noir Inquisitor
RANK_TIERS = [
    (20000, "LEGENDARY NOIR INQUISITOR", "GRADE SPECIAL", "MAX RANK"),
    (10000, "CHIEF OF DETECTIVES", "GRADE I", "20,000 PTS"),
    (6000, "SENIOR INSPECTOR", "GRADE II", "10,000 PTS"),
    (3000, "BEAT DETECTIVE", "GRADE III", "6,000 PTS"),
    (1000, "JUNIOR GUMSHOE", "GRADE IV", "3,000 PTS"),
    (0, "PATROL OFFICER", "GRADE V", "1,000 PTS"),
]

def get_detective_rank(score: int) -> Dict[str, str]:
    """Return rank title, official grade tier, and next milestone for a given career score."""
    score = max(0, int(score))
    for threshold, title, tier, next_tier in RANK_TIERS:
        if score >= threshold:
            return {
                "rank": title,
                "tier": tier,
                "next_tier": next_tier,
                "threshold": threshold
            }
    return {
        "rank": "PATROL OFFICER",
        "tier": "GRADE V",
        "next_tier": "1,000 PTS",
        "threshold": 0
    }

def calculate_score(
    won: bool,
    remaining_tokens: int,
    turns_taken: int,
    hint_used: bool = False,
    difficulty: str = "classic",
    streak: int = 1
) -> Dict[str, Any]:
    """
    Calculate granular detective score for a completed case.
    
    Formula:
    - Base Catch: +1,000 PTS
    - Token Efficiency: +250 PTS per unused token
    - Quick Deduction: +500 PTS if solved in <= 2 turns
    - Flawless Deduction: +250 PTS if solved without using any hint
    - Streak Incentive: +100 PTS per consecutive day (capped at 1,000 PTS)
    - Difficulty Multiplier:
        * Hardboiled: 1.5x
        * Classic: 1.0x
        * Rookie: 0.8x
    """
    if not won:
        return {
            "base": 0,
            "tokens_bonus": 0,
            "tokens_left": remaining_tokens,
            "quick_bonus": 0,
            "turns_taken": turns_taken,
            "flawless_bonus": 0,
            "hint_used": hint_used,
            "streak_bonus": 0,
            "streak": streak,
            "multiplier": 1.0,
            "difficulty": difficulty,
            "total": 0
        }

    base = 1000
    tokens_bonus = max(0, int(remaining_tokens)) * 250
    quick_bonus = 500 if turns_taken <= 2 else 0
    flawless_bonus = 250 if not hint_used else 0
    streak_bonus = min(max(1, streak) * 100, 1000)

    diff_mult = {
        "hardboiled": 1.5,
        "classic": 1.0,
        "rookie": 0.8
    }.get(difficulty.lower(), 1.0)

    subtotal = base + tokens_bonus + quick_bonus + flawless_bonus + streak_bonus
    total = int(round(subtotal * diff_mult))

    return {
        "base": base,
        "tokens_bonus": tokens_bonus,
        "tokens_left": remaining_tokens,
        "quick_bonus": quick_bonus,
        "turns_taken": turns_taken,
        "flawless_bonus": flawless_bonus,
        "hint_used": hint_used,
        "streak_bonus": streak_bonus,
        "streak": streak,
        "multiplier": diff_mult,
        "difficulty": difficulty,
        "total": total
    }

