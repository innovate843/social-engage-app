import aiosqlite
import datetime
import os

DB_PATH = os.getenv("DB_PATH", "engage.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    logged_in INTEGER DEFAULT 0,
    last_checked TEXT
);

CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'facebook',
    profile_url TEXT UNIQUE NOT NULL,
    birthday_month INTEGER,
    birthday_day INTEGER,
    last_wished_year INTEGER
);

CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    platform TEXT NOT NULL,
    target_name TEXT,
    target_profile_url TEXT,
    post_url TEXT,
    post_content TEXT,
    draft_message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    posted_at TEXT
);
"""

PLATFORMS_SEED = [
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("linkedin", "LinkedIn"),
    ("twitter", "X / Twitter"),
]


class Database:
    async def init(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript(SCHEMA)
            for pid, name in PLATFORMS_SEED:
                await db.execute(
                    "INSERT OR IGNORE INTO platforms (id, display_name) VALUES (?, ?)",
                    (pid, name),
                )
            await db.commit()

    async def get_queue(self, status: str = None, type: str = None):
        query = "SELECT * FROM queue WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if type:
            query += " AND type = ?"
            params.append(type)
        query += " ORDER BY created_at DESC"
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def get_queue_item(self, item_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM queue WHERE id = ?", (item_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def add_queue_item(self, item: dict):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO queue
                   (type, platform, target_name, target_profile_url, post_url, post_content, draft_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("type"), item.get("platform"), item.get("target_name"),
                    item.get("target_profile_url"), item.get("post_url"),
                    item.get("post_content"), item.get("draft_message"),
                ),
            )
            await db.commit()

    async def update_draft(self, item_id: int, draft_message: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE queue SET draft_message = ? WHERE id = ?",
                (draft_message, item_id),
            )
            await db.commit()

    async def set_status(self, item_id: int, status: str):
        async with aiosqlite.connect(DB_PATH) as db:
            if status == "posted":
                await db.execute(
                    "UPDATE queue SET status = ?, posted_at = datetime('now') WHERE id = ?",
                    (status, item_id),
                )
            else:
                await db.execute(
                    "UPDATE queue SET status = ? WHERE id = ?", (status, item_id)
                )
            await db.commit()

    async def get_platforms(self):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM platforms") as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def set_platform_logged_in(self, platform: str, logged_in: bool):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE platforms SET logged_in = ?, last_checked = datetime('now') WHERE id = ?",
                (1 if logged_in else 0, platform),
            )
            await db.commit()

    async def add_birthday(self, b: dict):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT OR REPLACE INTO birthdays
                   (name, platform, profile_url, birthday_month, birthday_day)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    b.get("name"), b.get("platform", "facebook"),
                    b.get("profile_url"), b.get("birthday_month"), b.get("birthday_day"),
                ),
            )
            await db.commit()

    async def get_todays_birthdays(self):
        today = datetime.date.today()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM birthdays
                   WHERE birthday_month = ? AND birthday_day = ?
                   AND (last_wished_year IS NULL OR last_wished_year < ?)""",
                (today.month, today.day, today.year),
            ) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def mark_birthday_wished(self, birthday_id: int, year: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE birthdays SET last_wished_year = ? WHERE id = ?",
                (year, birthday_id),
            )
            await db.commit()
