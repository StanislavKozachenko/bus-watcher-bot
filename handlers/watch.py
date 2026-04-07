import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import TIME_RANGES, TZ
from services.smilebus import SmileBusAPI
from services.watcher import run_watch

logger = logging.getLogger(__name__)

# Conversation states
FROM_CITY, TO_CITY, DATE, TIME_MANUAL_START, TIME_MANUAL_END, CONFIRM = range(6)

_CHUNK = 3  # buttons per row


def _city_keyboard(cities: dict[int, str]) -> InlineKeyboardMarkup:
    items = sorted(cities.items(), key=lambda x: x[1])
    rows = [
        [InlineKeyboardButton(name, callback_data=f"city:{cid}") for cid, name in items[i: i + _CHUNK]]
        for i in range(0, len(items), _CHUNK)
    ]
    return InlineKeyboardMarkup(rows)


def _date_keyboard() -> InlineKeyboardMarkup:
    tz = ZoneInfo(TZ)
    today = datetime.now(tz).date()
    buttons = [
        [
            InlineKeyboardButton("Сегодня", callback_data=f"date:{today.strftime('%d.%m.%Y')}"),
            InlineKeyboardButton("Завтра", callback_data=f"date:{(today + timedelta(days=1)).strftime('%d.%m.%Y')}"),
            InlineKeyboardButton("+2 дня", callback_data=f"date:{(today + timedelta(days=2)).strftime('%d.%m.%Y')}"),
        ],
        [InlineKeyboardButton("✏️ Ввести дату", callback_data="date:manual")],
    ]
    return InlineKeyboardMarkup(buttons)


def _time_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"time:{start}|{end}")]
        for start, end, label in TIME_RANGES
    ]
    rows.append([InlineKeyboardButton("✏️ Ввести вручную", callback_data="time:manual")])
    return InlineKeyboardMarkup(rows)


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Запустить", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm:no"),
        ]
    ])


# ------- Handlers -------

async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    api: SmileBusAPI = context.bot_data["api"]
    cities = api.all_cities()
    await update.message.reply_text("Выбери город отправления:", reply_markup=_city_keyboard(cities))
    return FROM_CITY


async def select_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    city_id = int(query.data.split(":")[1])
    context.user_data["from_id"] = city_id

    api: SmileBusAPI = context.bot_data["api"]
    dests = api.destinations(city_id)
    if not dests:
        await query.edit_message_text("Нет доступных направлений из этого города.")
        return ConversationHandler.END

    from_name = api.city_name(city_id)
    await query.edit_message_text(
        f"Откуда: {from_name}\nВыбери город назначения:",
        reply_markup=_city_keyboard(dests),
    )
    return TO_CITY


async def select_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    city_id = int(query.data.split(":")[1])
    context.user_data["to_id"] = city_id

    api: SmileBusAPI = context.bot_data["api"]
    from_name = api.city_name(context.user_data["from_id"])
    to_name = api.city_name(city_id)

    await query.edit_message_text(
        f"Откуда: {from_name}\nКуда: {to_name}\nВыбери дату:",
        reply_markup=_date_keyboard(),
    )
    return DATE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]

    if value == "manual":
        await query.edit_message_text("Введи дату (ДД.ММ.ГГГГ):")
        context.user_data["awaiting"] = "date"
        return DATE

    context.user_data["date"] = value
    await query.edit_message_text(
        f"Дата: {value}\nВыбери диапазон времени:",
        reply_markup=_time_keyboard(),
    )
    return TIME_MANUAL_START


async def manual_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text("Неверный формат. Введи дату (ДД.ММ.ГГГГ):")
        return DATE

    context.user_data["date"] = text
    await update.message.reply_text(
        f"Дата: {text}\nВыбери диапазон времени:",
        reply_markup=_time_keyboard(),
    )
    return TIME_MANUAL_START


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]

    if value == "manual":
        await query.edit_message_text("Введи время начала (ЧЧ:ММ):")
        return TIME_MANUAL_START

    start, end = value.split("|")
    context.user_data["start_time"] = start
    context.user_data["end_time"] = end
    return await _show_confirm(update, context)


async def manual_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text("Неверный формат. Введи время начала (ЧЧ:ММ):")
        return TIME_MANUAL_START

    context.user_data["start_time"] = text
    await update.message.reply_text("Введи время окончания (ЧЧ:ММ):")
    return TIME_MANUAL_END


async def manual_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text("Неверный формат. Введи время окончания (ЧЧ:ММ):")
        return TIME_MANUAL_END

    context.user_data["end_time"] = text
    return await _show_confirm(update, context)


async def _show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    api: SmileBusAPI = context.bot_data["api"]
    ud = context.user_data
    from_name = api.city_name(ud["from_id"])
    to_name = api.city_name(ud["to_id"])

    text = (
        f"Подтверди запуск мониторинга:\n\n"
        f"Маршрут: {from_name} → {to_name}\n"
        f"Дата: {ud['date']}\n"
        f"Время: {ud['start_time']} — {ud['end_time']}"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=_confirm_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=_confirm_keyboard())
    return CONFIRM


async def confirm_watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "confirm:no":
        await query.edit_message_text("❌ Отменено.")
        return ConversationHandler.END

    ud = context.user_data
    db = context.bot_data["db"]
    api: SmileBusAPI = context.bot_data["api"]
    active_tasks: dict = context.bot_data["active_tasks"]
    user_id = update.effective_user.id

    watch_id = await db.add_watch(
        user_id, ud["date"], ud["start_time"], ud["end_time"],
        ud["from_id"], ud["to_id"],
    )

    task = asyncio.create_task(
        run_watch(
            watch_id, user_id, ud["date"], ud["start_time"], ud["end_time"],
            ud["from_id"], ud["to_id"], context.bot, db, api,
        )
    )
    active_tasks[watch_id] = task

    from_name = api.city_name(ud["from_id"])
    to_name = api.city_name(ud["to_id"])

    await query.edit_message_text(
        f"🔍 Мониторинг запущен!\n\n"
        f"Маршрут: {from_name} → {to_name}\n"
        f"Дата: {ud['date']}\n"
        f"Время: {ud['start_time']} — {ud['end_time']}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


def build_watch_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("watch", cmd_watch),
            MessageHandler(filters.Regex("^🔍 Следить за билетами$"), cmd_watch),
        ],
        states={
            FROM_CITY: [CallbackQueryHandler(select_from_city, pattern=r"^city:")],
            TO_CITY: [CallbackQueryHandler(select_to_city, pattern=r"^city:")],
            DATE: [
                CallbackQueryHandler(select_date, pattern=r"^date:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_date_input),
            ],
            TIME_MANUAL_START: [
                CallbackQueryHandler(select_time, pattern=r"^time:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_time_start),
            ],
            TIME_MANUAL_END: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_time_end),
            ],
            CONFIRM: [CallbackQueryHandler(confirm_watch, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
