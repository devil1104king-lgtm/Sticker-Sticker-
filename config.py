import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", 0))

    # Validate required config
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables.")
    if not OWNER_ID:
        raise ValueError("OWNER_ID is not set in environment variables.")
    if not REQUIRED_CHANNEL:
        raise ValueError("REQUIRED_CHANNEL is not set in environment variables.")
    if not LOG_GROUP_ID:
        raise ValueError("LOG_GROUP_ID is not set in environment variables.")
