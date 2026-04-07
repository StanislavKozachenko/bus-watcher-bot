from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["🔍 Следить за билетами", "📋 Мои задачи"], ["❓ Помощь"]],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие или введи команду",
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я — бот мониторинга SmileBus.\n\n"
        "Используй кнопки внизу или вводи команды вручную.",
        reply_markup=MAIN_KEYBOARD,
    )


HELP_TEXT = (
    "📖 Справка\n\n"
    "/watch — запустить мониторинг билетов:\n"
    "  1. Выбери город отправления\n"
    "  2. Выбери город назначения\n"
    "  3. Выбери дату\n"
    "  4. Выбери диапазон времени (или введи вручную)\n"
    "  5. Подтверди — бот будет проверять каждые 10 сек\n\n"
    "/list — список твоих задач с кнопкой остановки\n"
    "/stop <id> — остановить мониторинг по ID\n"
    "/help — эта справка"
)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Не понял 🤔\n\n{HELP_TEXT}")
