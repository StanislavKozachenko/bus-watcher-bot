import asyncio
import logging
from datetime import datetime, timedelta

import pytz

from locales import t
from services.smilebus import SmileBusAPI

logger = logging.getLogger(__name__)


def _find_in_range(schedule: list, start_time_str: str, end_time_str: str, min_seats: int = 1) -> dict | None:
    start = datetime.strptime(start_time_str, "%H:%M").time()
    end = datetime.strptime(end_time_str, "%H:%M").time()
    for item in schedule:
        t_val = datetime.strptime(item["time"], "%H:%M").time()
        if start <= t_val <= end and item["count"] >= min_seats:
            return item
    return None


async def run_watch(
    watch_id: int,
    user_id: int,
    date: str,
    start_time: str,
    end_time: str,
    city_from_id: int,
    city_to_id: int,
    bot,
    db,
    api: SmileBusAPI,
    min_seats: int = 1,
) -> None:
    lang = await db.get_user_lang(user_id)
    tz = pytz.timezone("Europe/Minsk")
    trip_date = datetime.strptime(date, "%d.%m.%Y").date()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    deadline = tz.localize(datetime.combine(trip_date, end_time_obj)) - timedelta(minutes=30)

    logger.info("Watch #%d started, deadline %s", watch_id, deadline)

    while True:
        now = datetime.now(tz)
        if now >= deadline:
            await bot.send_message(user_id, t(lang, "watch_expired", date=date))
            await db.deactivate_watch(watch_id)
            return

        try:
            schedule = await api.fetch_schedule(date, city_from_id, city_to_id)
            found = _find_in_range(schedule, start_time, end_time, min_seats)
            if found:
                await bot.send_message(
                    chat_id=user_id,
                    text=t(lang, "tickets_found",
                           date=date, time=found["time"],
                           count=found["count"], route=found["route_name"]),
                )
                await db.deactivate_watch(watch_id)
                await db.add_history(f"Watch {watch_id}: found at {found['time']}")
                return
        except Exception as e:
            logger.warning("Watch #%d: API error (%s), retrying in 30s", watch_id, e)
            await asyncio.sleep(30)
            continue

        await asyncio.sleep(10)
