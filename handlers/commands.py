from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from locales import get_lang, t


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[t(lang, "keyboard_watch"), t(lang, "keyboard_list")], [t(lang, "keyboard_help")]],
        resize_keyboard=True,
        input_field_placeholder=t(lang, "keyboard_placeholder"),
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    await update.message.reply_text(
        t(lang, "start_greeting"),
        reply_markup=main_keyboard(lang),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    await update.message.reply_text(t(lang, "help_text"))


async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    await update.message.reply_text(t(lang, "unknown_msg") + t(lang, "help_text"))
