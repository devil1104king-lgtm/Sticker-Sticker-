import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # can be empty
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", 0))

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set.")
    if not OWNER_ID:
        raise ValueError("OWNER_ID is not set.")
    # REQUIRED_CHANNEL and LOG_GROUP_ID are optional
