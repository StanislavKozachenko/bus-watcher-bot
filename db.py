import aiosqlite
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class Database:
    def __init__(self, path):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS watches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    end_time TEXT,
                    city_from_id INTEGER,
                    city_to_id INTEGER,
                    start_time TEXT,
                    active INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    message TEXT
                )
            """)
            await db.commit()

    async def add_history(self, msg: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO history (timestamp, message) VALUES (?, ?)",
                (datetime.datetime.now().isoformat(), msg)
            )
            await db.commit()

    async def add_watch(self, user_id, date, start_time, end_time, city_from_id, city_to_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO watches (user_id, date, start_time, end_time, city_from_id, city_to_id, active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                (user_id, date, start_time, end_time, city_from_id, city_to_id)
            )
            await db.commit()

    async def deactivate_watch(self, watch_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE watches SET active = 0 WHERE id = ?", (watch_id,))
            await db.commit()

    async def get_active_watches(self):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT id, user_id, date, start_time, end_time, city_from_id, city_to_id FROM watches WHERE active = 1")
            return await cursor.fetchall()

    async def list_watches(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, date, start_time, end_time, city_from_id, city_to_id, active FROM watches WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchall()

    async def cleanup_old_watches(self):
        """
        Деактивирует все активные Watch-записи, где дата поездки прошла на день и более.
        """
        tz = ZoneInfo("Europe/Minsk")
        today = datetime.now(tz).date()

        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT id, date FROM watches WHERE active = 1")
            rows = await cursor.fetchall()
            for watch_id, date_str in rows:
                trip_date = datetime.strptime(date_str, "%d.%m.%Y").date()
                if trip_date < today - timedelta(days=1):
                    await db.execute("UPDATE watches SET active = 0 WHERE id = ?", (watch_id,))
            await db.commit()
