import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ==========================
    # BOT
    # ==========================
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    # ==========================
    # ADMINS
    # ==========================
    ADMINS = [
        int(x)
        for x in os.getenv("ADMINS", "").split(",")
        if x.strip().isdigit()
    ]

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    # ==========================
    # DATABASE
    # ==========================
    DATABASE_NAME = os.getenv(
        "DATABASE_NAME",
        "sticker_game.db"
    )

    # ==========================
    # CHANNELS
    # ==========================
    FORCE_SUB_CHANNEL = os.getenv(
        "FORCE_SUB_CHANNEL",
        ""
    )

    LOG_CHANNEL = os.getenv(
        "LOG_CHANNEL",
        ""
    )

    # ==========================
    # GAME
    # ==========================
    START_COINS = int(
        os.getenv("START_COINS", "100")
    )

    DAILY_REWARD = int(
        os.getenv("DAILY_REWARD", "50")
    )

    WIN_REWARD = int(
        os.getenv("WIN_REWARD", "10")
    )

    LOSE_PENALTY = int(
        os.getenv("LOSE_PENALTY", "5")
    )

    MAX_LEVEL = int(
        os.getenv("MAX_LEVEL", "100")
    )

    XP_PER_WIN = int(
        os.getenv("XP_PER_WIN", "15")
    )

    XP_PER_LOSS = int(
        os.getenv("XP_PER_LOSS", "5")
    )

    # ==========================
    # REFERRAL
    # ==========================
    REFERRAL_REWARD = int(
        os.getenv("REFERRAL_REWARD", "100")
    )

    # ==========================
    # FLOOD CONTROL
    # ==========================
    MESSAGE_COOLDOWN = int(
        os.getenv("MESSAGE_COOLDOWN", "2")
    )

    # ==========================
    # WEB
    # ==========================
    PORT = int(
        os.getenv("PORT", "10000")
    )

    HOST = os.getenv(
        "HOST",
        "0.0.0.0"
    )

    # ==========================
    # LOGGING
    # ==========================
    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    # ==========================
    # DEBUG
    # ==========================
    DEBUG = (
        os.getenv("DEBUG", "False")
        .lower()
        == "true"
    )
