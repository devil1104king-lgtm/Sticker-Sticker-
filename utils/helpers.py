import math
from typing import Tuple

def xp_to_level(xp: int) -> Tuple[int, int, int]:
    """Calculate level, current level XP, and next level XP based on total XP."""
    level = int((math.sqrt(100 * (2 * xp + 25)) + 50) / 100)
    current_level_base_xp = 50 * (level ** 2) - 50 * level
    next_level_base_xp = 50 * ((level + 1) ** 2) - 50 * (level + 1)
    return level, xp - current_level_base_xp, next_level_base_xp - current_level_base_xp

def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"
