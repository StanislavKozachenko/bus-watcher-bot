# Bus Watcher Bot

A Telegram bot that monitors SmileBus ticket availability and sends a notification the moment seats become available on a selected route.

## Features

- **Step-by-step booking flow** — city, date, and time range selection via inline keyboards; all 33 SmileBus cities supported with route-aware destination filtering
- **Flexible time input** — choose a preset range (morning / afternoon / evening) or enter a custom start/end time manually
- **Live task list** — `/list` displays all watches in a single message with an inline stop button per active task
- **Auto-recovery** — active watches are restored automatically on bot restart
- **Stale task cleanup** — watches past their travel date are deactivated on startup
- **Resilient polling** — API errors trigger a 30-second retry instead of crashing the watch task

## Project Structure

```
main.py               — entry point; builds Application with post_init hook
config.py             — environment config (BOT_TOKEN, DB_PATH, TIME_RANGES)
db.py                 — async SQLite wrapper (aiosqlite)
handlers/
  commands.py         — /start (reply keyboard), /help, unknown message fallback
  watch.py            — ConversationHandler for /watch (FROM_CITY → TO_CITY → DATE → TIME → CONFIRM)
  list_handler.py     — /list, /stop, inline stop callback
services/
  smilebus.py         — SmileBusAPI: city cache, route graph, schedule fetch
  watcher.py          — background polling loop with retry logic
```

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```
BOT_TOKEN=your_telegram_bot_token
DATABASE_PATH=watcher.db
```

### 3. Run

```bash
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and main menu |
| `/watch` | Start a new ticket watch (guided dialog) |
| `/list` | View all watches with inline stop controls |
| `/stop <id>` | Stop a watch by ID |
| `/help` | Show usage instructions |

## Tech Stack

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 22.7
- [aiohttp](https://docs.aiohttp.org/)
- [aiosqlite](https://aiosqlite.omnilib.dev/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
