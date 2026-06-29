# Sticker Sticker Game Bot

A production-ready Telegram Sticker Battle Game bot built with Python, python-telegram-bot (v21+), and asynchronous SQLite (aiosqlite). Features robust economy, XP system, match histories, full admin panel, and seamless anti-spam handling.

## Features
- **Sticker Battles:** Users can challenge each other and bet virtual coins. Random winner logic with animated UI sequences.
- **Robust Economy:** Complete with Daily Rewards, Referrals, and robust transactional logging.
- **Leveling System:** Automatic XP distribution and level progression.
- **Admin Dashboard:** Full control with Broadcast, Balance adjustments, Ban/Unban logic, Backup, and remote Restart features.
- **Production Grade:** Asynchronous DB calls, Anti-Spam (memory cache cooldowns), strict exception handling.
- **Cloud Ready:** Out of the box configuration for Render.com (Flask Keep-Alive web server & background runner), VPS, and Railway.

## Deployment Instructions

### Local Development / VPS
1. Clone the repository.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your details (`BOT_TOKEN`, `OWNER_ID`, etc.).
4. Run the bot: `python bot.py`

### Render.com
1. Connect your GitHub repository to Render.
2. Create a new **Web Service**.
3. Select `Python 3` as the environment.
4. Render will automatically read `render.yaml` configuring `gunicorn` for the keep-alive ping and booting the `bot.py` script as a background process simultaneously.
5. Setup the required Environment Variables in the Render Dashboard (`BOT_TOKEN`, `OWNER_ID`).

## File Structure Overview
- `bot.py` - Core execution and routing.
- `database.py` - Asynchronous SQLite connection manager and CRUD methods.
- `web.py` - Keep-alive Flask server for Platform-as-a-Service providers.
- `handlers/` - Bot command handlers broken down into modules (start, game, admin, callbacks, etc).
- `utils/` - Global utility scripts (backup chron-jobs, decorators, rate-limiting, and XP algorithms).
- `keyboards/` - Inline and Reply markup layouts.
cd sticker-bot
