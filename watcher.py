import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz

API_URL = "https://smilebus.by/api/v2/route/schedule-detail"

async def fetch_schedule(date: str, city_from_id: int, city_to_id: int):
    params = {
        "city_from_id": city_from_id,
        "city_to_id": city_to_id,
        "date": date,
        "stop_from_id": "",
        "stop_to_id": "",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as resp:
            return await resp.json()

def check_schedule_in_range(schedule, start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()

    for item in schedule:
        t = datetime.strptime(item["time"], "%H:%M").time()
        if start_time <= t <= end_time and item["count"] > 0:
            return item
    return None

async def run_watch(watch_id, user_id, date, start_time, end_time, city_from_id, city_to_id, bot, db):
    """
    Мониторинг билетов с учётом часового пояса Минска и остановкой
    за 30 минут до конца времени рейса.
    Работает для будущих дат и не завершает мониторинг до дедлайна.
    """
    tz = pytz.timezone("Europe/Minsk")
    trip_date = datetime.strptime(date, "%d.%m.%Y").date()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()

    # Абсолютный дедлайн: конец времени рейса - 1 час
    deadline = tz.localize(datetime.combine(trip_date, end_time_obj)) - timedelta(minutes=30)

    print(f"[DEBUG] Мониторинг запущен для даты {date}, дедлайн {deadline}")

    while True:
        now = datetime.now(tz)
        if now >= deadline:
            await bot.send_message(
                user_id,
                f"⏱ Мониторинг по дате {date} завершён (истекло время наблюдения)."
            )
            await db.deactivate_watch(watch_id)
            return

        data = await fetch_schedule(date, city_from_id, city_to_id)
        if "schedule" in data:
            found = check_schedule_in_range(data["schedule"], start_time, end_time)
            if found:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🎉 Билеты найдены!\n"
                        f"Дата: {date}\n"
                        f"Время: {found['time']}\n"
                        f"Мест: {found['count']}\n"
                        f"Маршрут: {found['route_name']}"
                    )
                )
                await db.deactivate_watch(watch_id)
                await db.add_history(f"Watch {watch_id}: found at {found['time']}")
                return

        # Проверяем каждые 10 секунд
        await asyncio.sleep(10)
