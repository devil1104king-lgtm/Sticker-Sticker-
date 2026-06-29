import time
from typing import Dict, Tuple

class CooldownManager:
    """Manager to handle user command cooldowns in memory."""
    def __init__(self):
        self._cooldowns: Dict[int, Dict[str, float]] = {}

    def check(self, user_id: int, command: str, seconds: int) -> Tuple[bool, float]:
        """Check if user is on cooldown. Returns (is_on_cooldown, remaining_time)."""
        current_time = time.time()
        if user_id not in self._cooldowns:
            self._cooldowns[user_id] = {}
            
        last_used = self._cooldowns[user_id].get(command, 0)
        elapsed = current_time - last_used
        
        if elapsed < seconds:
            return True, seconds - elapsed
            
        self._cooldowns[user_id][command] = current_time
        return False, 0.0

cooldown_mgr = CooldownManager()
