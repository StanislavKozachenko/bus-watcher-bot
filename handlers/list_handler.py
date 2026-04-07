import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    api = context.bot_data["api"]
    user_id = update.effective_user.id
    rows = await db.list_watches(user_id)

    if not rows:
        await update.message.reply_text("Нет активных или завершённых задач.")
        return

    lines = []
    stop_buttons = []

    for w_id, date, start, end, from_id, to_id, active in rows:
        status = "🟢" if active else "⚪"
        from_name = api.city_name(from_id)
        to_name = api.city_name(to_id)
        lines.append(f"{status} <b>#{w_id}</b> {from_name} → {to_name}  {date}  {start}–{end}")
        if active:
            stop_buttons.append(
                [InlineKeyboardButton(f"🛑 Стоп #{w_id}", callback_data=f"stop:{w_id}")]
            )

    text = "📋 <b>Ваши задачи:</b>\n\n" + "\n".join(lines)
    keyboard = InlineKeyboardMarkup(stop_buttons) if stop_buttons else None
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Использование: /stop <watch_id>")
        return

    watch_id = int(context.args[0])
    await _stop_watch(watch_id, context)
    await update.message.reply_text("🛑 Мониторинг остановлен.")


async def stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    watch_id = int(query.data.split(":")[1])
    await _stop_watch(watch_id, context)
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(query.message.text + "\n\n🛑 Остановлено")


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
    ]
