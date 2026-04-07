import asyncio
import logging

from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
from db import Database
from handlers.commands import MAIN_KEYBOARD, cmd_start, cmd_help, cmd_unknown
from handlers.list_handler import build_list_handlers
from handlers.watch import build_watch_handler
from services.smilebus import SmileBusAPI
from services.watcher import run_watch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

db = Database()
api = SmileBusAPI()
active_tasks: dict = {}


async def post_init(application) -> None:
    await db.init()
    await db.cleanup_old_watches()
    await api.load_cities()

    application.bot_data["db"] = db
    application.bot_data["api"] = api
    application.bot_data["active_tasks"] = active_tasks

    await application.bot.set_my_commands([
        BotCommand("watch", "Следить за билетами"),
        BotCommand("list", "Мои задачи"),
        BotCommand("help", "Справка"),
        BotCommand("stop", "Остановить мониторинг"),
    ])

    watches = await db.get_active_watches()
    for w_id, user_id, date, start_time, end_time, city_from_id, city_to_id in watches:
        task = asyncio.create_task(
            run_watch(w_id, user_id, date, start_time, end_time,
                      city_from_id, city_to_id, application.bot, db, api)
        )
        active_tasks[w_id] = task
        logger.info("Restored watch #%d", w_id)


if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(build_watch_handler())
    for handler in build_list_handlers():
        app.add_handler(handler)

    # Кнопки главного меню
    from handlers.list_handler import cmd_list
    app.add_handler(MessageHandler(filters.Regex("^📋 Мои задачи$"), cmd_list))
    app.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), cmd_help))

    # Fallback: любое нераспознанное сообщение или команда → справка
    app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, cmd_unknown))

    logger.info("Bot starting")
    app.run_polling(drop_pending_updates=True)
