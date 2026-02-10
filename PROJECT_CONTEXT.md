# Project Context: inbox_bot

> **Last Updated:** 2026-02-10
> **Version:** 1.1.0
> **Status:** Production Ready

---

## 1. Project Overview

**Name:** inbox_bot  
**Type:** Telegram Bot  
**Language:** Python 3.11  
**Framework:** python-telegram-bot v20.7

### Purpose
A Telegram bot that integrates with Notion API to allow users to quickly save notes/messages directly to their Notion Inbox page. The bot enables seamless note-taking by forwarding Telegram messages to a designated Notion page as to-do items.

### Key Features
- 🔐 **Authentication:** Notion Integration Token
- 📄 **Page Setup:** By URL or page name
- ✍️ **Note Taking:** Automatic to-do creation in Notion
- 🔔 **Scheduled Notifications:** Daily/weekly inbox summaries
- 🔄 **Version Management:** Shows new features on updates

---

## 2. Architecture

### Pattern
Modular monolithic application with clear separation of concerns.

### Data Flow
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│   User      │───▶│   Telegram   │───▶│    bot.py    │───▶│  database.py │───▶│ notion_api.py│
│ (Telegram)  │    │    Bot API   │    │   Handlers   │    │    SQLite    │    │ Notion API   │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────────┘
                                                                                           │
                                                                                           ▼
                                                                                    ┌──────────────┐
                                                                                    │ Notion Page  │
                                                                                    │  (Inbox)     │
                                                                                    └──────────────┘
```

---

## 3. Directory Structure

```
inbox_bot/
├── src/                          # Source code
│   ├── __init__.py              # Package init
│   ├── bot.py                   # Main entry point (627 lines)
│   ├── database.py              # SQLite operations (307 lines)
│   ├── notion_api.py            # Notion API client (259 lines)
│   ├── notifications.py         # APScheduler notifications (137 lines)
│   └── version.py               # Version management (45 lines)
├── tests/                        # Test files
│   ├── __init__.py
│   └── test_notion_api.py       # Notion API tests
├── data/                         # SQLite database storage
│   └── bot.db                   # User configuration database
├── .opencode/                    # AI assistant configuration
│   └── plans/                   # Implementation plans
├── scripts/                      # Deployment scripts
│   ├── deploy.sh
│   └── update.sh
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image configuration
├── docker-compose.yml            # Docker Compose setup
├── .env                         # Environment variables (not in git)
├── example.env                  # Environment template
├── README.md                    # Main documentation (Russian)
├── DOCKER.md                    # Docker-specific instructions
├── DESCRIPTION.md               # Requirements specification
├── Makefile                     # Build automation
├── .gitignore                   # Git exclusions
└── .dockerignore                # Docker build exclusions
```

---

## 4. Module Details

### bot.py (Main Entry Point)
**Lines:** 627  
**Responsibilities:**
- Telegram bot initialization
- Command handlers (/start, /list, /notifications, /reset, /help, /version)
- Conversation handlers (multi-step setup)
- Message routing
- Inline keyboard callbacks
- Main() function - application entry point

**Key Functions:**
- `main()` - Application entry point
- `start()` - /start command handler
- `handle_notion_token()` - Step 1 of setup
- `handle_page_input()` - Step 2 of setup
- `handle_message()` - Process notes
- `notifications_command()` - Configure notifications
- `list_notes()` - Show last 20 notes
- `check_and_show_changelog()` - Version check

**States (ConversationHandler):**
```python
WAITING_FOR_NOTION_TOKEN = 0
WAITING_FOR_PAGE = 1
SETTING_NOTIFICATIONS = 3
WAITING_FOR_NOTIFICATION_TIME = 4
WAITING_FOR_NOTIFICATION_DAYS = 5
```

---

### database.py (Data Layer)
**Lines:** 307  
**Responsibilities:**
- SQLite database operations
- User configuration management
- Notification settings storage
- Database migrations

**Key Methods:**
```python
# User Configuration
get_user_config(user_id) → dict
save_notion_token(user_id, token)
save_page_config(user_id, page_id, page_name)
reset_user_config(user_id)

# Notification Settings
save_notification_settings(user_id, enabled, time, days)
get_notification_settings(user_id) → dict
get_users_with_notifications() → list

# Version Management
get_user_version(user_id) → str
set_user_version(user_id, version)

# Database Migrations
migrate_add_notification_fields()
migrate_add_version_field()
migrate_from_intro_shown()
```

**Database Schema:**
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    notion_token TEXT,
    page_id TEXT,
    page_name TEXT,
    notification_enabled BOOLEAN DEFAULT 0,
    notification_time TEXT,
    notification_days TEXT DEFAULT '1,2,3,4,5',
    last_seen_version TEXT DEFAULT '0.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### notion_api.py (Notion Integration)
**Lines:** 259  
**Responsibilities:**
- Notion API authentication
- Page lookup by URL or name
- Content appending (to_do blocks)
- Page content reading

**Key Methods:**
```python
set_token(token)                    # Authenticate
test_connection()                   # Verify token
extract_page_id_from_url(url)       # Parse Notion URL
find_page_by_name(name)             # Search pages
get_page_info(page_id)              # Get page details
append_to_page(page_id, content)    # Add to-do item
get_page_content(page_id, limit=20) # Read page content
```

**Content Format:**
Messages are appended as `to_do` blocks (checkboxes) with `checked: false`.

---

### notifications.py (Scheduled Notifications)
**Lines:** 137  
**Responsibilities:**
- APScheduler integration
- Cron-based job scheduling
- Daily/weekly inbox summaries
- User-specific notification times

**Key Methods:**
```python
start()                              # Start scheduler
schedule_user(user_id, time, days)   # Schedule for user
unschedule_user(user_id)             # Remove schedule
update_user_schedule(user_id, ...)   # Update schedule
send_notification(user_id)           # Send summary
```

**Schedule Format:**
- Time: "HH:00" format (07:00-22:00)
- Days: "1,2,3,4,5" (1=Mon, 7=Sun)
- Cron expression: day_of_week='mon,tue,wed,thu,fri', hour=9, minute=0

**Notification Message:**
```
📬 Неразобранный инбокс (3 задачи):

☐ Купить молоко
☐ Позвонить клиенту
☐ Подготовить отчет

💡 Используйте /list для просмотра всех заметок
```

Or if empty:
```
🎉 Ваш инбокс пуст! Вы молодец!
```

---

### version.py (Version Management)
**Lines:** 45  
**Responsibilities:**
- Version constants
- Changelog storage
- Version comparison utilities

**Current Version:** 1.1.0

**Changelog:**
```python
CHANGELOG = {
    "1.1.0": {
        "features": [
            "📬 Система уведомлений о неразобранном инбоксе",
            "⏰ Настройка времени и дней рассылки уведомлений",
            "🔔 Команда /notifications для управления уведомлениями"
        ],
        "message": "🎉 Новое в версии 1.1.0:\n\n📬 Уведомления о неразобранном инбоксе!"
    },
    "1.0.0": {
        "features": ["🚀 Первый релиз"],
        "message": "👋 Добро пожаловать в бота для Notion Inbox!"
    }
}
```

**Utility Functions:**
```python
parse_version(version_str) → tuple           # "1.1.0" → (1, 1, 0)
is_newer_version(current, user) → bool       # Compare versions
should_show_notifications_intro(v) → bool    # v < 1.1.0?
get_changelog_message(version) → str         # Get changelog text
```

---

## 5. Dependencies

### requirements.txt
```
python-telegram-bot==20.7    # Telegram Bot API wrapper
notion-client==2.7.0         # Official Notion API client
pytest==7.4.3               # Testing framework
python-dotenv==1.0.0        # Environment variables
APScheduler==3.10.4         # Job scheduling
```

### Key Dependency Features
- **python-telegram-bot:** Async support, ConversationHandler, inline keyboards
- **notion-client:** Official Notion API SDK
- **APScheduler:** Cron triggers, persistent jobs
- **pytest:** Test discovery, fixtures

---

## 6. Bot Commands

| Command | Description | Handler Function |
|---------|-------------|------------------|
| `/start` | Begin setup or show config | `start()` |
| `/list` | Show last 20 notes from Notion | `list_notes()` |
| `/notifications` | Configure scheduled summaries | `notifications_command()` |
| `/reset` | Reset user configuration | `reset()` |
| `/help` | Show help message | `help_command()` |
| `/version` | Show bot version | `version_command()` |
| `/cancel` | Cancel current operation | `cancel()` |

---

## 7. Configuration

### Environment Variables

**Required:**
```bash
TELEGRAM_BOT_TOKEN=your_token_here    # From @BotFather
```

**Optional:**
```bash
DOCKER_ENV=true                       # Auto-set in Docker
DATA_DIR=/app/data                    # Database directory
PYTHONPATH=/app                       # For module imports
NOTION_TEST_TOKEN=secret_xxx          # For testing
```

### Docker Configuration

**Dockerfile:**
- Base image: `python:3.11-slim`
- Working dir: `/app`
- Entry point: `python -m src.bot`
- Volume: `./data:/app/data`

**docker-compose.yml:**
```yaml
services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## 8. Entry Points

### Development
```bash
# Local run
python -m src.bot

# With env file
export $(cat .env | xargs) && python -m src.bot
```

### Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Makefile Commands
```bash
make up       # Start bot
make down     # Stop bot
make logs     # View logs
make rebuild  # Full rebuild
```

---

## 9. Testing

### Test Structure
```
tests/
├── __init__.py
└── test_notion_api.py
```

### Running Tests
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_notion_api.py -v

# With coverage
pytest tests/ -v --cov=src
```

### Test Requirements
- `NOTION_TEST_TOKEN` environment variable
- Valid Notion integration with test page

### Current Tests
- `test_notion_get_user_data()` - Verify API connection and user name

---

## 10. User Workflow

### First Time Setup
1. User sends `/start`
2. Bot requests Notion Integration Token
3. User provides token (format: `secret_...`)
4. Bot validates token via Notion API
5. Bot requests target page (URL or name)
6. User provides page information
7. Bot validates page access
8. Configuration saved to SQLite

### Daily Usage
1. User sends any text message to bot
2. Bot validates user configuration
3. Bot appends message as to-do to Notion page
4. Bot confirms: "✅ Заметка записана"

### Notification Setup
1. User sends `/notifications`
2. Bot shows current settings
3. User selects time from inline keyboard (07:00-22:00)
4. User selects days from inline keyboard
5. Bot saves settings and schedules job
6. Bot sends daily summaries at specified time

---

## 11. Error Handling

### Common Errors & Messages

**Authorization Error (401):**
```
❌ Ошибка авторизации в Notion.

Возможные причины:
• Токен стал недействительным
• Интеграция была удалена

Используйте /reset для перенастройки.
```

**Page Not Found (404):**
```
❌ Страница не найдена.

Возможные причины:
• Страница была удалена
• У интеграции нет доступа к странице

Используйте /reset для перенастройки.
```

**Permission Error (403):**
```
❌ Нет доступа к странице.

Убедитесь, что:
• Интеграция добавлена на страницу
• У интеграции есть права на редактирование

Используйте /reset для перенастройки.
```

---

## 12. Recent Changes

### v1.1.0 (Current)
- ✅ Added notification system with APScheduler
- ✅ Added `/notifications` command
- ✅ Added version management system
- ✅ Added `/version` command
- ✅ Added `/list` command to view notes
- ✅ Reorganized project to `/src` structure
- ✅ Preserved git history with `git mv`

### Previous Versions
- **v1.0.0:** Initial release with basic note-taking

---

## 13. Future Improvements

### Planned Refactoring
Split `bot.py` (627 lines) into smaller modules:
1. **initialization.py** - Bot setup, database init
2. **handlers.py** - Command handlers
3. **keyboards.py** - Inline keyboard utilities
4. **utils.py** - Helper functions

### Potential Features
- [ ] Support for different block types (not just to_do)
- [ ] Tagging system
- [ ] Multiple pages per user
- [ ] Export functionality
- [ ] Webhook support (instead of polling)
- [ ] Admin panel
- [ ] Analytics/statistics

---

## 14. Development Guidelines

### Code Style
- **Type hints:** Use for function parameters and returns
- **Docstrings:** Google style for all public functions
- **Logging:** Use `logger = logging.getLogger(__name__)`
- **Error handling:** Try/except with specific error messages
- **Async/await:** All handlers are async

### Git Workflow
1. Create feature branch
2. Make changes
3. Run tests
4. Commit with descriptive messages
5. Push and create PR

### Database Migrations
When adding new fields:
1. Add migration method to `database.py`
2. Call it in `init_database()`
3. Handle existing data gracefully

---

## 15. Deployment Checklist

- [ ] Set `TELEGRAM_BOT_TOKEN` in `.env`
- [ ] Ensure `data/` directory exists
- [ ] Run `docker-compose build`
- [ ] Run `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Test bot with `/start`
- [ ] Verify database migrations run successfully
- [ ] Check notification scheduler starts

---

## 16. Troubleshooting

### Bot not responding
- Check `TELEGRAM_BOT_TOKEN` is correct
- Check logs: `docker-compose logs -f`
- Ensure only one instance is running

### Database errors
- Check `data/` directory permissions
- Verify database migrations ran
- Check SQLite file integrity

### Notion API errors
- Verify token starts with `secret_`
- Check integration has page access
- Ensure page exists and is accessible

### Notification issues
- Check APScheduler logs
- Verify `notification_time` format (HH:00)
- Check `notification_days` format (1,2,3,4,5)

---

## 17. Contact & Support

**Project:** inbox_bot  
**Created for:** Personal use  
**Repository:** `/Users/r3tam/dev/self/inbox_bot`

---

*This context file should be updated whenever significant changes are made to the project.*
