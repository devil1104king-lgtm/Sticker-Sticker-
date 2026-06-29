import aiosqlite
import time
from typing import Any, Dict, List, Optional, Tuple
from config import Config

class Database:
    """Asynchronous database manager using aiosqlite."""
    def __init__(self, db_path: str = Config.DATABASE_NAME):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Initialize all required database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    coins INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    total_games INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.0,
                    ref_count INTEGER DEFAULT 0,
                    ref_by INTEGER DEFAULT 0,
                    daily_reward_time REAL DEFAULT 0,
                    inventory TEXT DEFAULT 'default_pack',
                    current_pack TEXT DEFAULT 'default_pack',
                    is_banned INTEGER DEFAULT 0,
                    join_date REAL,
                    last_seen REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id INTEGER,
                    player2_id INTEGER,
                    winner_id INTEGER,
                    bet_amount INTEGER,
                    status TEXT,
                    created_at REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    referred_id INTEGER UNIQUE,
                    created_at REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    user_id INTEGER PRIMARY KEY,
                    last_claim_time REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    reason TEXT,
                    created_at REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    pack_name TEXT,
                    PRIMARY KEY (user_id, pack_name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_id INTEGER,
                    timestamp REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS broadcast_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    total_sent INTEGER,
                    timestamp REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS match_history (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id INTEGER,
                    player2_id INTEGER,
                    winner_id INTEGER,
                    timestamp REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[aiosqlite.Row]:
        """Fetch a user by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()

    async def create_user(self, user_id: int, username: str, first_name: str, ref_by: int = 0) -> bool:
        """Create a new user if they don't exist."""
        current_time = time.time()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if await cursor.fetchone():
                return False
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, coins, ref_by, join_date, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, Config.STARTING_COINS, ref_by, current_time, current_time))
            await db.commit()
            return True

    async def update_user(self, user_id: int, **kwargs: Any) -> None:
        """Update specific fields for a user dynamically."""
        if not kwargs:
            return
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", tuple(values))
            await db.commit()

    async def update_coins(self, user_id: int, amount: int, reason: str = "") -> None:
        """Update a user's coin balance and log transaction."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("INSERT INTO transactions (user_id, amount, reason, created_at) VALUES (?, ?, ?, ?)",
                             (user_id, amount, reason, time.time()))
            await db.commit()
            
    async def get_top_users(self, order_by: str, limit: int = 10) -> List[aiosqlite.Row]:
        """Fetch top users based on a specific column."""
        allowed_columns = ["coins", "xp", "wins", "ref_count"]
        if order_by not in allowed_columns:
            raise ValueError("Invalid column for ordering")
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"SELECT * FROM users ORDER BY {order_by} DESC LIMIT ?", (limit,))
            return await cursor.fetchall()

    async def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Process a referral."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("INSERT INTO referrals (user_id, referred_id, created_at) VALUES (?, ?, ?)",
                                 (referrer_id, referred_id, time.time()))
                await db.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referrer_id,))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def record_match(self, player1_id: int, player2_id: int, winner_id: int) -> None:
        """Record a completed match."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO match_history (player1_id, player2_id, winner_id, timestamp)
                VALUES (?, ?, ?, ?)
            """, (player1_id, player2_id, winner_id, time.time()))
            await db.commit()

    async def execute_query(self, query: str, params: Tuple = ()) -> Any:
        """Execute arbitrary query (Admin only)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return await cursor.fetchall()
            await db.commit()
            return cursor.rowcount

db = Database()
              
