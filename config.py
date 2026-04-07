import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_PATH: str = os.getenv("DATABASE_PATH", "watcher.db")
TZ: str = "Europe/Minsk"

TIME_RANGES = [
    ("06:00", "10:00"),
    ("10:00", "14:00"),
    ("14:00", "18:00"),
    ("18:00", "22:00"),
]

# City IDs shown as a pinned row at the top of the city picker
FEATURED_CITY_IDS: list[int] = [1]  # 1 = Минск

LIST_PAGE_SIZE: int = 8
