import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import LIST_PAGE_SIZE
from locales import get_lang, t

logger = logging.getLogger(__name__)


def _sort_key(row):
    """Active first, then by travel date descending."""
    w_id, date, start, end, from_id, to_id, active = row
    try:
        parsed = datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        parsed = datetime.min
    return (0 if active else 1, -parsed.timestamp())


def _build_list_message(rows: list, page: int, api, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    total = len(rows)
    active_count = sum(1 for r in rows if r[6])

    sorted_rows = sorted(rows, key=_sort_key)
    total_pages = max(1, (total + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    page_rows = sorted_rows[page * LIST_PAGE_SIZE:(page + 1) * LIST_PAGE_SIZE]

    header = t(lang, "list_header", active=active_count, total=total)

    lines = []
    last_group = None
    for row in page_rows:
        w_id, date, start, end, from_id, to_id, active = row
        group = "active" if active else "done"
        if group != last_group:
            lines.append(t(lang, "section_active") if active else t(lang, "section_completed"))
            last_group = group
        from_name = api.city_name(from_id)
        to_name = api.city_name(to_id)
        icon = "🟢" if active else "⚪"
        lines.append(f"{icon} <b>#{w_id}</b> {from_name} → {to_name}  {date}  {start}–{end}")

    text = header + "\n".join(lines)

    buttons = []

    for row in page_rows:
        w_id, date, start, end, from_id, to_id, active = row
        if active:
            buttons.append([InlineKeyboardButton(
                t(lang, "btn_stop", watch_id=w_id), callback_data=f"stop:{w_id}"
            )])

    if any(not r[6] for r in rows):
        buttons.append([InlineKeyboardButton(t(lang, "btn_clear_completed"), callback_data="list_clear")])

    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"list_page:{page - 1}"))
        nav.append(InlineKeyboardButton(f"{page + 1} / {total_pages}", callback_data="list_noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"list_page:{page + 1}"))
        buttons.append(nav)

    return text, InlineKeyboardMarkup(buttons)


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    api = context.bot_data["api"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    rows = await db.list_watches(user_id)

    if not rows:
        await update.message.reply_text(t(lang, "no_watches"))
        return

    text, keyboard = _build_list_message(rows, page=0, api=api, lang=lang)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def list_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])

    db = context.bot_data["db"]
    api = context.bot_data["api"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    rows = await db.list_watches(user_id)

    text, keyboard = _build_list_message(rows, page=page, api=api, lang=lang)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


async def list_clear_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    db = context.bot_data["db"]
    api = context.bot_data["api"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)

    deleted = await db.delete_completed_watches(user_id)
    rows = await db.list_watches(user_id)

    if not rows:
        await query.edit_message_text(t(lang, "cleared_no_active", count=deleted))
        return

    text, keyboard = _build_list_message(rows, page=0, api=api, lang=lang)
    text = t(lang, "cleared_prefix", count=deleted) + text
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    if not context.args:
        await update.message.reply_text("Usage: /stop <watch_id>")
        return
    watch_id = int(context.args[0])
    await _stop_watch(watch_id, context)
    await update.message.reply_text(t(lang, "watch_stopped"))


async def stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    watch_id = int(query.data.split(":")[1])
    await _stop_watch(watch_id, context)

    db = context.bot_data["db"]
    api = context.bot_data["api"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    rows = await db.list_watches(user_id)

    if not rows:
        await query.edit_message_text(t(lang, "stopped_no_watches"))
        return

    text, keyboard = _build_list_message(rows, page=0, api=api, lang=lang)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


async def _stop_watch(watch_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    active_tasks: dict = context.bot_data["active_tasks"]
    db = context.bot_data["db"]
    task = active_tasks.pop(watch_id, None)
    if task:
        task.cancel()
    await db.deactivate_watch(watch_id)
    logger.info("Watch #%d stopped", watch_id)


def build_list_handlers():
    return [
        CommandHandler("list", cmd_list),
        CommandHandler("stop", cmd_stop),
        CallbackQueryHandler(stop_callback, pattern=r"^stop:\d+$"),
        CallbackQueryHandler(list_page_callback, pattern=r"^list_page:\d+$"),
        CallbackQueryHandler(list_clear_callback, pattern=r"^list_clear$"),
        CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r"^list_noop$"),
    ]
