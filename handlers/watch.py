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

from config import FEATURED_CITY_IDS, TIME_RANGES, TZ
from locales import get_lang, t
from services.smilebus import SmileBusAPI
from services.watcher import run_watch

logger = logging.getLogger(__name__)

# Conversation states
FROM_CITY, TO_CITY, DATE, TIME_MANUAL_START, TIME_MANUAL_END, SEATS, CONFIRM = range(7)

_CHUNK = 3  # buttons per row


def _city_keyboard(cities: dict[int, str], lang: str) -> InlineKeyboardMarkup:
    featured = [(cid, f"⭐ {name}") for cid, name in cities.items() if cid in FEATURED_CITY_IDS]
    regular = sorted(
        [(cid, name) for cid, name in cities.items() if cid not in FEATURED_CITY_IDS],
        key=lambda x: x[1],
    )
    rows = []
    if featured:
        rows.append([InlineKeyboardButton(name, callback_data=f"city:{cid}") for cid, name in featured])
    rows += [
        [InlineKeyboardButton(name, callback_data=f"city:{cid}") for cid, name in regular[i: i + _CHUNK]]
        for i in range(0, len(regular), _CHUNK)
    ]
    rows.append([InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="watch_cancel")])
    return InlineKeyboardMarkup(rows)


def _date_keyboard(lang: str) -> InlineKeyboardMarkup:
    tz = ZoneInfo(TZ)
    today = datetime.now(tz).date()
    buttons = [
        [
            InlineKeyboardButton(t(lang, "btn_today"), callback_data=f"date:{today.strftime('%d.%m.%Y')}"),
            InlineKeyboardButton(t(lang, "btn_tomorrow"), callback_data=f"date:{(today + timedelta(days=1)).strftime('%d.%m.%Y')}"),
            InlineKeyboardButton(t(lang, "btn_plus2"), callback_data=f"date:{(today + timedelta(days=2)).strftime('%d.%m.%Y')}"),
        ],
        [InlineKeyboardButton(t(lang, "btn_enter_date"), callback_data="date:manual")],
        [InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="watch_cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def _time_keyboard(lang: str) -> InlineKeyboardMarkup:
    labels = t(lang, "time_range_labels")
    rows = [
        [InlineKeyboardButton(label, callback_data=f"time:{start}|{end}")]
        for (start, end), label in zip(TIME_RANGES, labels)
    ]
    rows.append([InlineKeyboardButton(t(lang, "btn_enter_manual"), callback_data="time:manual")])
    rows.append([InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="watch_cancel")])
    return InlineKeyboardMarkup(rows)


def _seats_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data="seats:1"),
            InlineKeyboardButton("2", callback_data="seats:2"),
            InlineKeyboardButton("3", callback_data="seats:3"),
        ],
        [InlineKeyboardButton(t(lang, "btn_enter_manual"), callback_data="seats:manual")],
        [InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="watch_cancel")],
    ])


def _confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(lang, "btn_run"), callback_data="confirm:yes"),
            InlineKeyboardButton(t(lang, "btn_confirm_cancel"), callback_data="watch_cancel"),
        ]
    ])


# ------- Handlers -------

async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = context.bot_data["db"]
    api: SmileBusAPI = context.bot_data["api"]
    lang = await get_lang(update.effective_user.id, context, db)
    cities = api.all_cities()
    await update.message.reply_text(t(lang, "select_from_city"), reply_markup=_city_keyboard(cities, lang))
    return FROM_CITY


async def select_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    city_id = int(query.data.split(":")[1])
    context.user_data["from_id"] = city_id

    db = context.bot_data["db"]
    api: SmileBusAPI = context.bot_data["api"]
    lang = await get_lang(update.effective_user.id, context, db)
    dests = api.destinations(city_id)
    if not dests:
        await query.edit_message_text(t(lang, "no_destinations"))
        return ConversationHandler.END

    from_name = api.city_name(city_id)
    await query.edit_message_text(
        t(lang, "select_to_city", from_name=from_name),
        reply_markup=_city_keyboard(dests, lang),
    )
    return TO_CITY


async def select_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    city_id = int(query.data.split(":")[1])
    context.user_data["to_id"] = city_id

    db = context.bot_data["db"]
    api: SmileBusAPI = context.bot_data["api"]
    lang = await get_lang(update.effective_user.id, context, db)
    from_name = api.city_name(context.user_data["from_id"])
    to_name = api.city_name(city_id)

    await query.edit_message_text(
        t(lang, "select_date", from_name=from_name, to_name=to_name),
        reply_markup=_date_keyboard(lang),
    )
    return DATE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]

    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)

    if value == "manual":
        await query.edit_message_text(t(lang, "enter_date_manual"))
        context.user_data["awaiting"] = "date"
        return DATE

    context.user_data["date"] = value
    await query.edit_message_text(
        t(lang, "select_time", date=value),
        reply_markup=_time_keyboard(lang),
    )
    return TIME_MANUAL_START


async def manual_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)
    try:
        datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(t(lang, "date_invalid"))
        return DATE

    context.user_data["date"] = text
    await update.message.reply_text(
        t(lang, "select_time", date=text),
        reply_markup=_time_keyboard(lang),
    )
    return TIME_MANUAL_START


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]

    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)

    if value == "manual":
        await query.edit_message_text(t(lang, "enter_time_start"))
        return TIME_MANUAL_START

    start, end = value.split("|")
    context.user_data["start_time"] = start
    context.user_data["end_time"] = end
    return await _show_seats(update, context, lang)


async def manual_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text(t(lang, "time_start_invalid"))
        return TIME_MANUAL_START

    context.user_data["start_time"] = text
    await update.message.reply_text(t(lang, "enter_time_end"))
    return TIME_MANUAL_END


async def manual_time_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await update.message.reply_text(t(lang, "time_end_invalid"))
        return TIME_MANUAL_END

    context.user_data["end_time"] = text
    return await _show_seats(update, context, lang)


async def _show_seats(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> int:
    text = t(lang, "select_seats")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=_seats_keyboard(lang))
    else:
        await update.message.reply_text(text, reply_markup=_seats_keyboard(lang))
    return SEATS


async def select_seats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":")[1]
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)

    if value == "manual":
        await query.edit_message_text(t(lang, "enter_seats_manual"))
        return SEATS

    context.user_data["min_seats"] = int(value)
    return await _show_confirm(update, context, lang)


async def manual_seats_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)

    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text(t(lang, "seats_invalid"))
        return SEATS

    context.user_data["min_seats"] = int(text)
    return await _show_confirm(update, context, lang)


async def _show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> int:
    api: SmileBusAPI = context.bot_data["api"]
    ud = context.user_data
    from_name = api.city_name(ud["from_id"])
    to_name = api.city_name(ud["to_id"])

    text = t(lang, "confirm_text", from_name=from_name, to_name=to_name,
             date=ud["date"], start=ud["start_time"], end=ud["end_time"],
             min_seats=ud["min_seats"])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=_confirm_keyboard(lang))
    else:
        await update.message.reply_text(text, reply_markup=_confirm_keyboard(lang))
    return CONFIRM


async def confirm_watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    ud = context.user_data
    db = context.bot_data["db"]
    api: SmileBusAPI = context.bot_data["api"]
    active_tasks: dict = context.bot_data["active_tasks"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)

    watch_id = await db.add_watch(
        user_id, ud["date"], ud["start_time"], ud["end_time"],
        ud["from_id"], ud["to_id"], ud["min_seats"],
    )

    task = asyncio.create_task(
        run_watch(
            watch_id, user_id, ud["date"], ud["start_time"], ud["end_time"],
            ud["from_id"], ud["to_id"], context.bot, db, api, ud["min_seats"],
        )
    )
    active_tasks[watch_id] = task

    from_name = api.city_name(ud["from_id"])
    to_name = api.city_name(ud["to_id"])

    await query.edit_message_text(
        t(lang, "watch_started_msg", from_name=from_name, to_name=to_name,
          date=ud["date"], start=ud["start_time"], end=ud["end_time"],
          min_seats=ud["min_seats"])
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)
    await update.message.reply_text(t(lang, "watch_cancelled"))
    return ConversationHandler.END


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    db = context.bot_data["db"]
    lang = await get_lang(update.effective_user.id, context, db)
    await query.edit_message_text(t(lang, "watch_cancelled"))
    return ConversationHandler.END


def build_watch_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("watch", cmd_watch),
            MessageHandler(filters.Regex("^🔍"), cmd_watch),
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
            SEATS: [
                CallbackQueryHandler(select_seats, pattern=r"^seats:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_seats_input),
            ],
            CONFIRM: [CallbackQueryHandler(confirm_watch, pattern=r"^confirm:")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_callback, pattern=r"^watch_cancel$"),
        ],
        per_message=False,
    )
