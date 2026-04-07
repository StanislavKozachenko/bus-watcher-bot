from __future__ import annotations

DEFAULT_LANG = "ru"

STRINGS: dict[str, dict] = {
    "ru": {
        "keyboard_watch": "🔍 Следить за билетами",
        "keyboard_list": "📋 Мои задачи",
        "keyboard_help": "❓ Помощь",
        "keyboard_placeholder": "Выбери действие или введи команду",
        "start_greeting": "Привет! Я — бот мониторинга SmileBus.\n\nИспользуй кнопки внизу или вводи команды вручную.",
        "help_text": (
            "📖 Справка\n\n"
            "/watch — запустить мониторинг билетов:\n"
            "  1. Выбери город отправления\n"
            "  2. Выбери город назначения\n"
            "  3. Выбери дату\n"
            "  4. Выбери диапазон времени (или введи вручную)\n"
            "  5. Подтверди — бот будет проверять каждые 10 сек\n\n"
            "/list — список твоих задач с кнопкой остановки\n"
            "/stop <id> — остановить мониторинг по ID\n"
            "/language — сменить язык\n"
            "/help — эта справка"
        ),
        "unknown_msg": "Не понял 🤔\n\n",
        "select_from_city": "Выбери город отправления:",
        "select_to_city": "Откуда: {from_name}\nВыбери город назначения:",
        "no_destinations": "Нет доступных направлений из этого города.",
        "select_date": "Откуда: {from_name}\nКуда: {to_name}\nВыбери дату:",
        "enter_date_manual": "Введи дату (ДД.ММ.ГГГГ):",
        "date_invalid": "Неверный формат. Введи дату (ДД.ММ.ГГГГ):",
        "select_time": "Дата: {date}\nВыбери диапазон времени:",
        "enter_time_start": "Введи время начала (ЧЧ:ММ):",
        "time_start_invalid": "Неверный формат. Введи время начала (ЧЧ:ММ):",
        "enter_time_end": "Введи время окончания (ЧЧ:ММ):",
        "time_end_invalid": "Неверный формат. Введи время окончания (ЧЧ:ММ):",
        "confirm_text": "Подтверди запуск мониторинга:\n\nМаршрут: {from_name} → {to_name}\nДата: {date}\nВремя: {start} — {end}",
        "watch_started_msg": "🔍 Мониторинг запущен!\n\nМаршрут: {from_name} → {to_name}\nДата: {date}\nВремя: {start} — {end}",
        "watch_cancelled": "❌ Отменено.",
        "btn_today": "Сегодня",
        "btn_tomorrow": "Завтра",
        "btn_plus2": "+2 дня",
        "btn_enter_date": "✏️ Ввести дату",
        "btn_enter_manual": "✏️ Ввести вручную",
        "btn_cancel": "❌ Cancel",
        "btn_run": "✅ Запустить",
        "btn_confirm_cancel": "❌ Отмена",
        "time_range_labels": ["Утро 06–10", "День 10–14", "День 14–18", "Вечер 18–22"],
        "no_watches": "Нет задач. Используй /watch для запуска.",
        "list_header": "📋 <b>Твои задачи</b>  •  Активных: {active} / Всего: {total}\n\n",
        "section_active": "🟢 <b>Активные</b>",
        "section_completed": "⚪ <b>Завершённые</b>",
        "btn_stop": "🛑 Стоп #{watch_id}",
        "btn_clear_completed": "🗑 Удалить завершённые",
        "stopped_no_watches": "🛑 Мониторинг остановлен. Задач больше нет.",
        "cleared_prefix": "🗑 Удалено {count} завершённых.\n\n",
        "cleared_no_active": "🗑 Удалено {count} завершённых. Активных задач нет.",
        "watch_stopped": "🛑 Мониторинг остановлен.",
        "watch_expired": "⏱ Мониторинг по дате {date} завершён (истекло время наблюдения).",
        "tickets_found": "🎉 Билеты найдены!\nДата: {date}\nВремя: {time}\nМест: {count}\nМаршрут: {route}",
        "lang_prompt": "Текущий язык: 🇷🇺 Русский\nВыбери язык:",
        "lang_set": "🇷🇺 Язык изменён на русский.",
    },
    "en": {
        "keyboard_watch": "🔍 Watch tickets",
        "keyboard_list": "📋 My watches",
        "keyboard_help": "❓ Help",
        "keyboard_placeholder": "Choose action or type a command",
        "start_greeting": "Hi! I'm SmileBus monitoring bot.\n\nUse the buttons below or type commands.",
        "help_text": (
            "📖 Help\n\n"
            "/watch — start ticket monitoring:\n"
            "  1. Choose departure city\n"
            "  2. Choose destination city\n"
            "  3. Choose date\n"
            "  4. Choose time range (or enter manually)\n"
            "  5. Confirm — bot checks every 10 sec\n\n"
            "/list — your watches with stop button\n"
            "/stop <id> — stop watch by ID\n"
            "/language — change language\n"
            "/help — this help"
        ),
        "unknown_msg": "I don't understand 🤔\n\n",
        "select_from_city": "Choose departure city:",
        "select_to_city": "From: {from_name}\nChoose destination city:",
        "no_destinations": "No available destinations from this city.",
        "select_date": "From: {from_name}\nTo: {to_name}\nChoose date:",
        "enter_date_manual": "Enter date (DD.MM.YYYY):",
        "date_invalid": "Wrong format. Enter date (DD.MM.YYYY):",
        "select_time": "Date: {date}\nChoose time range:",
        "enter_time_start": "Enter start time (HH:MM):",
        "time_start_invalid": "Wrong format. Enter start time (HH:MM):",
        "enter_time_end": "Enter end time (HH:MM):",
        "time_end_invalid": "Wrong format. Enter end time (HH:MM):",
        "confirm_text": "Confirm monitoring:\n\nRoute: {from_name} → {to_name}\nDate: {date}\nTime: {start} — {end}",
        "watch_started_msg": "🔍 Monitoring started!\n\nRoute: {from_name} → {to_name}\nDate: {date}\nTime: {start} — {end}",
        "watch_cancelled": "❌ Cancelled.",
        "btn_today": "Today",
        "btn_tomorrow": "Tomorrow",
        "btn_plus2": "+2 days",
        "btn_enter_date": "✏️ Enter date",
        "btn_enter_manual": "✏️ Enter manually",
        "btn_cancel": "❌ Cancel",
        "btn_run": "✅ Start",
        "btn_confirm_cancel": "❌ Cancel",
        "time_range_labels": ["Morning 06–10", "Afternoon 10–14", "Afternoon 14–18", "Evening 18–22"],
        "no_watches": "No watches yet. Use /watch to start monitoring.",
        "list_header": "📋 <b>Your watches</b>  •  Active: {active} / Total: {total}\n\n",
        "section_active": "🟢 <b>Active</b>",
        "section_completed": "⚪ <b>Completed</b>",
        "btn_stop": "🛑 Stop #{watch_id}",
        "btn_clear_completed": "🗑 Clear completed",
        "stopped_no_watches": "🛑 Watch stopped. No more watches.",
        "cleared_prefix": "🗑 Cleared {count} completed watch(es).\n\n",
        "cleared_no_active": "🗑 Cleared {count} completed watch(es). No active watches.",
        "watch_stopped": "🛑 Watch stopped.",
        "watch_expired": "⏱ Monitoring for {date} ended (time window expired).",
        "tickets_found": "🎉 Tickets found!\nDate: {date}\nTime: {time}\nSeats: {count}\nRoute: {route}",
        "lang_prompt": "Current language: 🇬🇧 English\nChoose language:",
        "lang_set": "🇬🇧 Language changed to English.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    s = STRINGS.get(lang, STRINGS[DEFAULT_LANG]).get(key, key)
    if kwargs and isinstance(s, str):
        return s.format(**kwargs)
    return s


async def get_lang(user_id: int, context, db) -> str:
    if "lang" not in context.user_data:
        context.user_data["lang"] = await db.get_user_lang(user_id)
    return context.user_data["lang"]
