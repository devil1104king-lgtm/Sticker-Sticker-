import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = "database/stickers.db"

async def get_db():
    """Return an aiosqlite connection."""
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    """Create tables if they don't exist."""
    async with get_db() as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP,
                selected_category TEXT,
                is_banned BOOLEAN DEFAULT 0,
                joined_channel BOOLEAN DEFAULT 0
            )
        """)
        # Categories
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                emoji TEXT,
                created_date TIMESTAMP,
                created_by INTEGER
            )
        """)
        # Stickers
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                file_id TEXT UNIQUE,
                file_unique_id TEXT UNIQUE,
                added_date TIMESTAMP,
                added_by INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        """)
        # User stats
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                total_stickers_sent INTEGER DEFAULT 0,
                total_stickers_received INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)
        await db.commit()

        # Insert default categories if not exist
        default_categories = [
            ("Normal", "😀"),
            ("Love", "❤️"),
            ("Dark", "💀"),
            ("Savage", "🔥"),
            ("Funny", "😂"),
            ("Attitude", "😎"),
            ("Meme", "🤣"),
            ("Random", "🎭")
        ]
        for name, emoji in default_categories:
            await db.execute(
                "INSERT OR IGNORE INTO categories (name, emoji, created_date, created_by) VALUES (?, ?, ?, ?)",
                (name, emoji, datetime.now(), 0)
            )
        await db.commit()

# ---- User Functions ----

async def register_user(user_id: int, username: str = None, first_name: str = None):
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, joined_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
            """,
            (user_id, username, first_name, datetime.now())
        )
        await db.execute(
            "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
            (user_id,)
        )
        await db.commit()

async def get_user(user_id: int) -> Optional[Dict]:
    async with get_db() as db:
        row = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = await row.fetchone()
        return dict(result) if result else None

async def set_user_category(user_id: int, category_name: str):
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET selected_category = ? WHERE user_id = ?",
            (category_name, user_id)
        )
        await db.commit()

async def get_user_category(user_id: int) -> Optional[str]:
    user = await get_user(user_id)
    return user.get("selected_category") if user else None

async def set_user_joined_channel(user_id: int, joined: bool):
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET joined_channel = ? WHERE user_id = ?",
            (joined, user_id)
        )
        await db.commit()

async def ban_user(user_id: int):
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def unban_user(user_id: int):
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def is_user_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user.get("is_banned")) if user else False

async def get_all_users() -> List[Dict]:
    async with get_db() as db:
        rows = await db.execute("SELECT * FROM users")
        return [dict(row) for row in await rows.fetchall()]

async def get_total_users() -> int:
    async with get_db() as db:
        row = await db.execute("SELECT COUNT(*) as count FROM users")
        result = await row.fetchone()
        return result["count"] if result else 0

# ---- Category Functions ----

async def get_all_categories() -> List[Dict]:
    async with get_db() as db:
        rows = await db.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in await rows.fetchall()]

async def get_category_by_name(name: str) -> Optional[Dict]:
    async with get_db() as db:
        row = await db.execute("SELECT * FROM categories WHERE name = ?", (name,))
        result = await row.fetchone()
        return dict(result) if result else None

async def get_category_by_id(cat_id: int) -> Optional[Dict]:
    async with get_db() as db:
        row = await db.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        result = await row.fetchone()
        return dict(result) if result else None

async def create_category(name: str, emoji: str = "", created_by: int = 0) -> bool:
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO categories (name, emoji, created_date, created_by) VALUES (?, ?, ?, ?)",
                (name, emoji, datetime.now(), created_by)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def delete_category(name: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM categories WHERE name = ?", (name,))
        await db.commit()
        return cursor.rowcount > 0

async def get_category_count() -> int:
    async with get_db() as db:
        row = await db.execute("SELECT COUNT(*) as count FROM categories")
        result = await row.fetchone()
        return result["count"] if result else 0

# ---- Sticker Functions ----

async def add_sticker(category_name: str, file_id: str, file_unique_id: str, added_by: int = 0) -> bool:
    category = await get_category_by_name(category_name)
    if not category:
        return False
    async with get_db() as db:
        try:
            await db.execute(
                """
                INSERT INTO stickers (category_id, file_id, file_unique_id, added_date, added_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category["id"], file_id, file_unique_id, datetime.now(), added_by)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def remove_sticker(sticker_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM stickers WHERE id = ?", (sticker_id,))
        await db.commit()
        return cursor.rowcount > 0

async def get_stickers_by_category(category_name: str) -> List[Dict]:
    category = await get_category_by_name(category_name)
    if not category:
        return []
    async with get_db() as db:
        rows = await db.execute(
            "SELECT * FROM stickers WHERE category_id = ? ORDER BY id",
            (category["id"],)
        )
        return [dict(row) for row in await rows.fetchall()]

async def get_random_sticker(category_name: str) -> Optional[str]:
    category = await get_category_by_name(category_name)
    if not category:
        return None
    async with get_db() as db:
        rows = await db.execute(
            "SELECT file_id FROM stickers WHERE category_id = ?",
            (category["id"],)
        )
        stickers = await rows.fetchall()
        if not stickers:
            return None
        import random
        choice = random.choice(stickers)
        return choice["file_id"]

async def get_total_stickers() -> int:
    async with get_db() as db:
        row = await db.execute("SELECT COUNT(*) as count FROM stickers")
        result = await row.fetchone()
        return result["count"] if result else 0

async def get_all_stickers() -> List[Dict]:
    async with get_db() as db:
        rows = await db.execute("""
            SELECT stickers.*, categories.name as category_name
            FROM stickers
            JOIN categories ON stickers.category_id = categories.id
            ORDER BY stickers.id
        """)
        return [dict(row) for row in await rows.fetchall()]

# ---- Stats Functions ----

async def increment_sticker_sent(user_id: int):
    async with get_db() as db:
        await db.execute(
            "UPDATE user_stats SET total_stickers_sent = total_stickers_sent + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def increment_sticker_received(user_id: int):
    async with get_db() as db:
        await db.execute(
            "UPDATE user_stats SET total_stickers_received = total_stickers_received + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def get_user_stats(user_id: int) -> Dict:
    async with get_db() as db:
        row = await db.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        result = await row.fetchone()
        return dict(result) if result else {"total_stickers_sent": 0, "total_stickers_received": 0}

# ---- Admin Helper ----

async def export_database() -> bytes:
    with open(DB_PATH, "rb") as f:
        return f.read()
