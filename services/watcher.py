import asyncio
import logging
from datetime import datetime, timedelta

import pytz

from services.smilebus import SmileBusAPI

logger = logging.getLogger(__name__)


def _find_in_range(schedule: list, start_time_str: str, end_time_str: str) -> dict | None:
    start = datetime.strptime(start_time_str, "%H:%M").time()
    end = datetime.strptime(end_time_str, "%H:%M").time()
    for item in schedule:
        t = datetime.strptime(item["time"], "%H:%M").time()
        if start <= t <= end and item["count"] > 0:
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
) -> None:
    tz = pytz.timezone("Europe/Minsk")
    trip_date = datetime.strptime(date, "%d.%m.%Y").date()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    deadline = tz.localize(datetime.combine(trip_date, end_time_obj)) - timedelta(minutes=30)

    logger.info("Watch #%d started, deadline %s", watch_id, deadline)

    while True:
        now = datetime.now(tz)
        if now >= deadline:
            await bot.send_message(
                user_id,
                f"⏱ Мониторинг по дате {date} завершён (истекло время наблюдения).",
            )
            await db.deactivate_watch(watch_id)
            return

        try:
            schedule = await api.fetch_schedule(date, city_from_id, city_to_id)
            found = _find_in_range(schedule, start_time, end_time)
            if found:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🎉 Билеты найдены!\n"
                        f"Дата: {date}\n"
                        f"Время: {found['time']}\n"
                        f"Мест: {found['count']}\n"
                        f"Маршрут: {found['route_name']}"
                    ),
                )
                await db.deactivate_watch(watch_id)
                await db.add_history(f"Watch {watch_id}: found at {found['time']}")
                return
        except Exception as e:
            logger.warning("Watch #%d: API error (%s), retrying in 30s", watch_id, e)
            await asyncio.sleep(30)
            continue

        await asyncio.sleep(10)
