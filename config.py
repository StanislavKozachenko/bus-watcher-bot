import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_PATH: str = os.getenv("DATABASE_PATH", "watcher.db")
TZ: str = "Europe/Minsk"

TIME_RANGES = [
    ("06:00", "10:00", "Утро 06–10"),
    ("10:00", "14:00", "День 10–14"),
    ("14:00", "18:00", "День 14–18"),
    ("18:00", "22:00", "Вечер 18–22"),
]
