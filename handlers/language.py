from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from locales import get_lang, t


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    user_id = update.effective_user.id
    lang = await get_lang(user_id, context, db)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
        ]
    ])
    await update.message.reply_text(t(lang, "lang_prompt"), reply_markup=keyboard)


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    new_lang = query.data.split(":")[1]
    db = context.bot_data["db"]
    await db.set_user_lang(update.effective_user.id, new_lang)
    context.user_data["lang"] = new_lang
    await query.edit_message_text(t(new_lang, "lang_set"))


def build_language_handlers():
    return [
        CommandHandler("language", cmd_language),
        CallbackQueryHandler(lang_callback, pattern=r"^lang:(ru|en)$"),
    ]
