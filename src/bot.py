#!/usr/bin/env python3
"""
Telegram бот для записи сообщений в Notion Inbox страницу.

Entry point for the bot. Initializes all components and starts polling.
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)

from src.app_globals import db, notification_manager
from src.notifications import NotificationManager
from src.notion_api import NotionClient
from src.handlers import (
    start,
    handle_notion_token,
    handle_page_input,
    handle_message,
    reset,
    list_notes,
    cancel,
    help_command,
    version_command,
    notifications_command,
    handle_notification_callback,
    WAITING_FOR_NOTION_TOKEN,
    WAITING_FOR_PAGE,
    SETTING_NOTIFICATIONS,
    WAITING_FOR_NOTIFICATION_TIME,
    WAITING_FOR_NOTIFICATION_DAYS,
    WAITING_FOR_TIMEZONE,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота."""
    # Получаем токен бота из переменной окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        print("Ошибка: Установите переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Инициализируем базу данных сначала (с миграциями)
    db.init_database()
    
    # Инициализируем менеджер уведомлений
    notion_client = NotionClient()
    notif_manager = NotificationManager(db, notion_client, application.bot)
    notif_manager.start()
    
    # Сохраняем в bot_data для доступа из обработчиков
    application.bot_data['notification_manager'] = notif_manager
    
    # Создаем ConversationHandler для настройки
    setup_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_NOTION_TOKEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notion_token)
            ],
            WAITING_FOR_PAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_page_input)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Создаем ConversationHandler для настройки уведомлений
    notifications_handler = ConversationHandler(
        entry_points=[CommandHandler('notifications', notifications_command)],
        states={
            SETTING_NOTIFICATIONS: [
                CallbackQueryHandler(handle_notification_callback, pattern='^(notif_|notif_change|notif_disable)')
            ],
            WAITING_FOR_TIMEZONE: [
                CallbackQueryHandler(handle_notification_callback, pattern='^tz_')
            ],
            WAITING_FOR_NOTIFICATION_TIME: [
                CallbackQueryHandler(handle_notification_callback, pattern='^time_')
            ],
            WAITING_FOR_NOTIFICATION_DAYS: [
                CallbackQueryHandler(handle_notification_callback, pattern='^(day_toggle_|days_done)')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Регистрируем обработчики
    application.add_handler(setup_handler)
    application.add_handler(notifications_handler)
    application.add_handler(CommandHandler('list', list_notes))
    application.add_handler(CommandHandler('reset', reset))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('version', version_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
