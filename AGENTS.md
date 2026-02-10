# AGENTS.md - AI Assistant Instructions

> **Project:** inbox_bot  
> **Type:** Telegram Bot for Notion Integration  
> **Last Updated:** 2026-02-10

---

## Quick Overview

**inbox_bot** — Telegram бот для быстрого сохранения заметок в Notion Inbox. Пользователь отправляет сообщение боту → оно появляется в Notion как чекбокс (to_do).

**Stack:** Python 3.11, python-telegram-bot v20.7, SQLite, Notion API, APScheduler

---

## Project Structure

```
src/
├── bot.py              # Entry point (627 lines)
├── database.py         # SQLite + migrations (307 lines)  
├── notion_api.py       # Notion API client (259 lines)
├── notifications.py    # APScheduler notifications (137 lines)
└── version.py          # Version management (45 lines)
```

---

## Common Commands

### Development
```bash
# Run locally
python -m src.bot

# Run tests  
pytest tests/test_notion_api.py -v

# With env
export $(cat .env | xargs) && python -m src.bot
```

### Docker
```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

---

## Key Components

### 1. Entry Point (`src/bot.py`)
- **Function:** `main()` — инициализация и запуск бота
- **Telegram token:** Из переменной `TELEGRAM_BOT_TOKEN`
- **Database:** Инициализируется перед NotificationManager

### 2. Database (`src/database.py`)
- **Path:** `data/bot.db` (SQLite)
- **Main table:** `users` с полями:
  - `user_id`, `notion_token`, `page_id`, `page_name`
  - `notification_enabled`, `notification_time`, `notification_days`
  - `last_seen_version`
- **Migrations:** Автоматические при старте (`migrate_*` методы)

### 3. Notion API (`src/notion_api.py`)
- **Token format:** `secret_...`
- **Page lookup:** По URL или названию
- **Content type:** Добавляет как `to_do` блоки (чекбоксы)
- **Method:** `append_to_page(page_id, content)`

### 4. Notifications (`src/notifications.py`)
- **Scheduler:** APScheduler с CronTrigger
- **Format:** Время "HH:00", дни "1,2,3,4,5" (1=пн)
- **Message:** Показывает неотмеченные чекбоксы или "Ваш инбокс пуст!"

---

## Bot Commands

| Command | Handler | Purpose |
|---------|---------|---------|
| `/start` | `start()` | Setup or show config |
| `/list` | `list_notes()` | Show last 20 notes |
| `/notifications` | `notifications_command()` | Configure notifications |
| `/reset` | `reset()` | Reset configuration |
| `/help` | `help_command()` | Show help |
| `/version` | `version_command()` | Show version |

---

## Important Patterns

### Conversation States
```python
WAITING_FOR_NOTION_TOKEN = 0      # Setup step 1
WAITING_FOR_PAGE = 1              # Setup step 2
SETTING_NOTIFICATIONS = 3         # Notification config
WAITING_FOR_NOTIFICATION_TIME = 4
WAITING_FOR_NOTIFICATION_DAYS = 5
```

### Global Variables (in bot.py)
```python
db = Database()                   # Database instance
notion_client = NotionClient()    # Notion API client
notification_manager = None       # Set in main()
```

### Version Management
- **Current version:** `1.1.0` (in `src/version.py`)
- **Field:** `users.last_seen_version`
- **Logic:** Если версия пользователя < 1.1.0 → показать intro о нотификациях

---

## Testing

### Test File
- **Location:** `tests/test_notion_api.py`
- **Requires:** `NOTION_TEST_TOKEN` env variable

### Run Tests
```bash
# Check if token exists
export NOTION_TEST_TOKEN="secret_..."

# Run
pytest tests/test_notion_api.py -v -s
```

---

## Database Migrations

When adding new fields, add migration method to `database.py`:

```python
def migrate_add_new_field(self):
    """Migration: add new_field to users table."""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    if 'new_field' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN new_field TEXT")
        conn.commit()
```

Then call it in `init_database()`.

---

## Common Tasks

### Add New Command
1. Define handler function in `src/bot.py`
2. Add to `main()`:
   ```python
   application.add_handler(CommandHandler('newcmd', new_command))
   ```
3. Add to `/help` message

### Add New Keyboard
```python
def get_new_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Text", callback_data="callback_data")]
    ])
```

### Handle New Callback
Add to `handle_notification_callback()` or create new handler.

---

## Troubleshooting

### "No such column" error
- **Cause:** Database schema outdated
- **Fix:** Миграция не выполнилась. Проверить `init_database()` вызывается ДО `notification_manager.start()`

### "Conflict: terminated by other getUpdates"
- **Cause:** Multiple bot instances running
- **Fix:** 
  ```bash
  docker-compose down
  sleep 30
  docker-compose up -d
  ```

### ModuleNotFoundError
- **Cause:** Files not copied in Docker
- **Fix:** Проверить Dockerfile копирует `src/` директорию

---

## Code Style

### Function Signature
```python
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Description.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        Conversation state or None
    """
    user_id = update.effective_user.id
    # Implementation
```

### Error Handling
```python
try:
    result = await some_operation()
except Exception as e:
    logger.error(f"Error in operation: {e}")
    await update.message.reply_text(f"❌ Error: {str(e)}")
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"User {user_id} did something")
logger.error(f"Error occurred: {e}")
```

---

## Dependencies

**Core:**
- `python-telegram-bot==20.7` — Telegram Bot API
- `notion-client==2.7.0` — Notion API
- `APScheduler==3.10.4` — Job scheduling

**Dev:**
- `pytest==7.4.3` — Testing
- `python-dotenv==1.0.0` — Environment variables

---

## Environment Variables

**Required:**
- `TELEGRAM_BOT_TOKEN` — From @BotFather

**Optional:**
- `DOCKER_ENV=true` — Auto-set in Docker
- `DATA_DIR=/app/data` — Database directory
- `PYTHONPATH=/app` — For imports
- `NOTION_TEST_TOKEN` — For testing

---

## Architecture Notes

### Data Flow
```
Telegram Message → bot.py → database.py → notion_api.py → Notion Page
```

### Notification Flow
```
APScheduler → notifications.py → bot.send_message() → Telegram
```

### Version Check Flow
```
/start → check_and_show_changelog() → 
  IF version < 1.1.0: show notification intro
  ELSE: show regular message
```

---

## File Locations

| File | Purpose |
|------|---------|
| `src/bot.py` | Main entry, handlers |
| `src/database.py` | SQLite operations |
| `src/notion_api.py` | Notion API client |
| `src/notifications.py` | Scheduled notifications |
| `src/version.py` | Version constants |
| `data/bot.db` | SQLite database |
| `tests/test_notion_api.py` | API tests |
| `PROJECT_CONTEXT.md` | Full documentation |

---

## When Working on This Project

1. **Always check PROJECT_CONTEXT.md** for detailed info
2. **Run tests** before committing: `pytest tests/`
3. **Update this file** if you add new patterns/commands
4. **Preserve git history** when moving files (use `git mv`)
5. **Test in Docker** before deploying: `docker-compose up --build`

---

**Need more details?** See `PROJECT_CONTEXT.md` for comprehensive documentation.
