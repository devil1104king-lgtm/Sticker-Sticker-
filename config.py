import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration from environment variables."""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
    
    # Parse comma-separated admin IDs
    _admins_env: str = os.getenv("ADMINS", "")
    ADMINS: List[int] = [int(x.strip()) for x in _admins_env.split(",")] if _admins_env else []
    if OWNER_ID and OWNER_ID not in ADMINS:
        ADMINS.append(OWNER_ID)
        
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "database.sqlite")
    FORCE_SUB_CHANNEL: int = int(os.getenv("FORCE_SUB_CHANNEL", "0"))
    LOG_CHANNEL: int = int(os.getenv("LOG_CHANNEL", "0"))
    PORT: int = int(os.getenv("PORT", "8080"))

    # Game Constants
    STARTING_COINS: int = 500
    DAILY_REWARD: int = 200
    REFERRAL_REWARD: int = 500
    GAME_REWARD_COINS: int = 100
    GAME_REWARD_XP: int = 50
    GAME_LOSER_PENALTY: int = 50
    DAILY_COOLDOWN: int = 86400  # 24 hours in seconds
