import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from db import Database
from watcher import run_watch

# -----------------------------
# Настройки
# -----------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DATABASE_PATH", "watcher.db")

db = Database(DB_PATH)
active_tasks = {}

# -----------------------------
# Handlers
# -----------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я — бот мониторинга SmileBus. Используй /watch, /list, /stop."
    )

async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 5:
        await update.message.reply_text(
            "Использование:\n"
            "/watch <city_from_id> <city_to_id> <дата> <начало_время> <конец_время>\n"
            "Пример:\n/watch 1 58 05.12.2025 18:00 21:10"
        )
        return

    city_from_id = int(context.args[0])
    city_to_id = int(context.args[1])
    date = context.args[2]
    start_time = context.args[3]
    end_time = context.args[4]
    user_id = update.effective_user.id

    new_watch_id = await db.add_watch(user_id, date, start_time, end_time, city_from_id, city_to_id)

    task = asyncio.create_task(
        run_watch(new_watch_id, user_id, date, start_time, end_time,
                  city_from_id, city_to_id, context.bot, db)
    )
    active_tasks[new_watch_id] = task

    city_from_name = "Минск" if city_from_id == 1 else f"ID {city_from_id}"
    city_to_name = "Рогачёв" if city_to_id == 58 else f"ID {city_to_id}"

    await update.message.reply_text(
        f"🔍 Мониторинг запущен.\nМаршрут: {city_from_name} → {city_to_name}\nДата: {date}\nВремя: {start_time} — {end_time}"
    )

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = await db.list_watches(user_id)
    if not rows:
        await update.message.reply_text("Нет активных или старых задач.")
        return

    msg = "📋 Ваши задачи:\n\n"
    for w_id, date, start, end, from_id, to_id, active in rows:
        status = "🟢 активна" if active else "⚪ завершена"
        from_name = "Минск" if from_id == 1 else f"ID {from_id}"
        to_name = "Рогачёв" if to_id == 58 else f"ID {to_id}"
        msg += f"ID {w_id}: {from_name} → {to_name}, {date} {start}-{end} — {status}\n"

    await update.message.reply_text(msg)

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Использование: /stop <watch_id>")
        return

    watch_id = int(context.args[0])
    if watch_id in active_tasks:
        active_tasks[watch_id].cancel()
        del active_tasks[watch_id]

    await db.deactivate_watch(watch_id)
    await update.message.reply_text("🛑 Мониторинг остановлен.")

# -----------------------------
# Инициализация при старте
# -----------------------------
async def post_init(application):
    await db.init()
    await db.cleanup_old_watches()
    watches = await db.get_active_watches()
    for w_id, user_id, date, start_time, end_time, city_from_id, city_to_id in watches:
        task = asyncio.create_task(
            run_watch(w_id, user_id, date, start_time, end_time,
                      city_from_id, city_to_id, application.bot, db)
        )
        active_tasks[w_id] = task

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    print("Running")
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .build())

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("watch", cmd_watch))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("stop", cmd_stop))

    print("Bot started")
    app.run_polling(drop_pending_updates=True)
