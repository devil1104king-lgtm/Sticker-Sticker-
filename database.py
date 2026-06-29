import sqlite3
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "database/stickers.db"

# ---- Helper for synchronous queries ----

def _execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(query, params)
    result = None
    if fetchone:
        result = c.fetchone()
    elif fetchall:
        result = c.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return result

# ---- Database initialisation ----

def _init_db_sync():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            emoji TEXT,
            created_date TIMESTAMP,
            created_by INTEGER
        )
    """)
    c.execute("""
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_stickers_sent INTEGER DEFAULT 0,
            total_stickers_received INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
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
        c.execute(
            "INSERT OR IGNORE INTO categories (name, emoji, created_date, created_by) VALUES (?, ?, ?, ?)",
            (name, emoji, datetime.now(), 0)
        )
    conn.commit()
    conn.close()

async def init_db():
    await asyncio.to_thread(_init_db_sync)

# ---- User Functions ----

async def register_user(user_id: int, username: str = None, first_name: str = None):
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO users (user_id, username, first_name, joined_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
            """,
            (user_id, username, first_name, datetime.now())
        )
        c.execute(
            "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)

async def get_user(user_id: int) -> Optional[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_)

async def set_user_category(user_id: int, category_name: str):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE users SET selected_category = ? WHERE user_id = ?",
        (category_name, user_id),
        commit=True
    )

async def get_user_category(user_id: int) -> Optional[str]:
    user = await get_user(user_id)
    return user.get("selected_category") if user else None

async def set_user_joined_channel(user_id: int, joined: bool):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE users SET joined_channel = ? WHERE user_id = ?",
        (joined, user_id),
        commit=True
    )

async def ban_user(user_id: int):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE users SET is_banned = 1 WHERE user_id = ?",
        (user_id,),
        commit=True
    )

async def unban_user(user_id: int):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE users SET is_banned = 0 WHERE user_id = ?",
        (user_id,),
        commit=True
    )

async def is_user_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user.get("is_banned")) if user else False

async def get_all_users() -> List[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return await asyncio.to_thread(_)

async def get_total_users() -> int:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM users")
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    return await asyncio.to_thread(_)

# ---- Category Functions ----

async def get_all_categories() -> List[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM categories ORDER BY name")
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return await asyncio.to_thread(_)

async def get_category_by_name(name: str) -> Optional[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM categories WHERE name = ?", (name,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_)

async def get_category_by_id(cat_id: int) -> Optional[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_)

async def create_category(name: str, emoji: str = "", created_by: int = 0) -> bool:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO categories (name, emoji, created_date, created_by) VALUES (?, ?, ?, ?)",
                (name, emoji, datetime.now(), created_by)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    return await asyncio.to_thread(_)

async def delete_category(name: str) -> bool:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM categories WHERE name = ?", (name,))
        rows = c.rowcount
        conn.commit()
        conn.close()
        return rows > 0
    return await asyncio.to_thread(_)

async def get_category_count() -> int:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM categories")
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    return await asyncio.to_thread(_)

# ---- Sticker Functions ----

async def add_sticker(category_name: str, file_id: str, file_unique_id: str, added_by: int = 0) -> bool:
    category = await get_category_by_name(category_name)
    if not category:
        return False
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO stickers (category_id, file_id, file_unique_id, added_date, added_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category["id"], file_id, file_unique_id, datetime.now(), added_by)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    return await asyncio.to_thread(_)

async def remove_sticker(sticker_id: int) -> bool:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM stickers WHERE id = ?", (sticker_id,))
        rows = c.rowcount
        conn.commit()
        conn.close()
        return rows > 0
    return await asyncio.to_thread(_)

async def get_stickers_by_category(category_name: str) -> List[Dict]:
    category = await get_category_by_name(category_name)
    if not category:
        return []
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM stickers WHERE category_id = ? ORDER BY id",
            (category["id"],)
        )
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return await asyncio.to_thread(_)

async def get_random_sticker(category_name: str) -> Optional[str]:
    category = await get_category_by_name(category_name)
    if not category:
        return None
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT file_id FROM stickers WHERE category_id = ?",
            (category["id"],)
        )
        stickers = c.fetchall()
        conn.close()
        if not stickers:
            return None
        import random
        choice = random.choice(stickers)
        return choice[0]
    return await asyncio.to_thread(_)

async def get_total_stickers() -> int:
    def _():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM stickers")
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    return await asyncio.to_thread(_)

async def get_all_stickers() -> List[Dict]:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT stickers.*, categories.name as category_name
            FROM stickers
            JOIN categories ON stickers.category_id = categories.id
            ORDER BY stickers.id
        """)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return await asyncio.to_thread(_)

# ---- Stats Functions ----

async def increment_sticker_sent(user_id: int):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE user_stats SET total_stickers_sent = total_stickers_sent + 1 WHERE user_id = ?",
        (user_id,),
        commit=True
    )

async def increment_sticker_received(user_id: int):
    await asyncio.to_thread(
        _execute_query,
        "UPDATE user_stats SET total_stickers_received = total_stickers_received + 1 WHERE user_id = ?",
        (user_id,),
        commit=True
    )

async def get_user_stats(user_id: int) -> Dict:
    def _():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else {"total_stickers_sent": 0, "total_stickers_received": 0}
    return await asyncio.to_thread(_)

# ---- Admin Helper ----

async def export_database() -> bytes:
    def _():
        with open(DB_PATH, "rb") as f:
            return f.read()
    return await asyncio.to_thread(_)
