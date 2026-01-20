#!/usr/bin/env python3
"""
Telegram бот для записи сообщений в Notion Inbox страницу.
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from database import Database
from notion_api import NotionClient

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_NOTION_TOKEN, WAITING_FOR_PAGE = range(2)

# Инициализация базы данных и Notion клиента
db = Database()
notion_client = NotionClient()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    
    # Проверяем, есть ли уже сохраненная конфигурация
    config = db.get_user_config(user_id)
    
    if config and config.get('notion_token') and config.get('page_id'):
        await update.message.reply_text(
            "✅ Вы уже настроили бота!\n\n"
            "Ваша конфигурация:\n"
            f"• Страница: {config.get('page_name', 'Не указано')}\n\n"
            "Просто отправьте сообщение, и оно будет добавлено в ваш Inbox.\n\n"
            "Используйте /reset для перенастройки."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "👋 Привет! Я помогу вам записывать заметки в ваш Notion Inbox.\n\n"
        "Для начала работы нужно:\n"
        "1. Подключить ваш Notion аккаунт\n"
        "2. Указать страницу для записи заметок\n\n"
        "📝 Отправьте ваш Notion Integration Token.\n\n"
        "Как получить токен:\n"
        "1. Перейдите на https://www.notion.so/my-integrations\n"
        "2. Создайте новую интеграцию\n"
        "3. Скопируйте Internal Integration Token\n"
        "4. Отправьте его мне\n\n"
        "Или отправьте /cancel для отмены."
    )
    return WAITING_FOR_NOTION_TOKEN


async def handle_notion_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка токена Notion."""
    user_id = update.effective_user.id
    token = update.message.text.strip()
    
    # Валидация токена (базовая проверка формата)
    if not token or len(token) < 20:
        await update.message.reply_text(
            "❌ Токен выглядит некорректно. Пожалуйста, проверьте и отправьте правильный токен.\n\n"
            "Токен должен начинаться с 'secret_' и быть длинным."
        )
        return WAITING_FOR_NOTION_TOKEN
    
    # Проверяем токен через Notion API
    try:
        test_client = NotionClient()
        test_client.set_token(token)
        # Пробуем получить информацию о пользователе
        test_client.test_connection()
        
        # Сохраняем токен
        db.save_notion_token(user_id, token)
        
        await update.message.reply_text(
            "✅ Токен успешно сохранен!\n\n"
            "Теперь укажите страницу для записи заметок.\n\n"
            "Вы можете отправить:\n"
            "• Ссылку на страницу (URL)\n"
            "• Или название страницы (если она находится в вашей рабочей области)\n\n"
            "Или отправьте /cancel для отмены."
        )
        return WAITING_FOR_PAGE
        
    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при проверке токена: {str(e)}\n\n"
            "Проверьте:\n"
            "• Правильность токена\n"
            "• Что интеграция активирована\n"
            "• Что у интеграции есть доступ к нужным страницам\n\n"
            "Попробуйте отправить токен еще раз или /cancel для отмены."
        )
        return WAITING_FOR_NOTION_TOKEN


async def handle_page_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода страницы."""
    user_id = update.effective_user.id
    page_input = update.message.text.strip()
    
    config = db.get_user_config(user_id)
    if not config or not config.get('notion_token'):
        await update.message.reply_text(
            "❌ Токен не найден. Пожалуйста, начните с команды /start."
        )
        return ConversationHandler.END
    
    try:
        notion_client.set_token(config['notion_token'])
        
        # Определяем, это URL или название страницы
        page_id = None
        page_name = None
        
        if page_input.startswith('http'):
            # Это URL, извлекаем page_id
            page_id = notion_client.extract_page_id_from_url(page_input)
            if not page_id:
                raise ValueError("Не удалось извлечь ID страницы из URL")
        else:
            # Это название страницы, ищем её
            page_id, page_name = notion_client.find_page_by_name(page_input)
            if not page_id:
                raise ValueError(f"Страница '{page_input}' не найдена")
        
        # Проверяем доступ к странице и получаем её название
        if not page_name:
            page_info = notion_client.get_page_info(page_id)
            page_name = page_info.get('title', 'Без названия')
        
        # Сохраняем конфигурацию
        db.save_page_config(user_id, page_id, page_name)
        
        await update.message.reply_text(
            f"✅ Страница успешно настроена!\n\n"
            f"📄 Страница: {page_name}\n\n"
            "Теперь просто отправляйте мне сообщения, и я буду добавлять их в ваш Inbox.\n\n"
            "Используйте /reset для перенастройки."
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка при настройке страницы: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при настройке страницы: {str(e)}\n\n"
            "Возможные причины:\n"
            "• Страница не найдена\n"
            "• У интеграции нет доступа к этой странице\n"
            "• Неверный формат URL или названия\n\n"
            "Попробуйте еще раз или /cancel для отмены."
        )
        return WAITING_FOR_PAGE


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений для записи в Notion."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Проверяем конфигурацию пользователя
    config = db.get_user_config(user_id)
    
    if not config or not config.get('notion_token') or not config.get('page_id'):
        await update.message.reply_text(
            "⚠️ Бот не настроен. Используйте /start для начала настройки."
        )
        return
    
    try:
        notion_client.set_token(config['notion_token'])
        
        # Добавляем заметку в Notion
        notion_client.append_to_page(
            page_id=config['page_id'],
            content=message_text
        )
        
        await update.message.reply_text("✅ Заметка записана")
        
    except Exception as e:
        logger.error(f"Ошибка при записи в Notion: {e}")
        error_message = str(e)
        
        # Более понятные сообщения об ошибках
        if "unauthorized" in error_message.lower() or "401" in error_message:
            error_text = (
                "❌ Ошибка авторизации в Notion.\n\n"
                "Возможные причины:\n"
                "• Токен стал недействительным\n"
                "• Интеграция была удалена\n\n"
                "Используйте /reset для перенастройки."
            )
        elif "not found" in error_message.lower() or "404" in error_message:
            error_text = (
                "❌ Страница не найдена.\n\n"
                "Возможные причины:\n"
                "• Страница была удалена\n"
                "• У интеграции нет доступа к странице\n\n"
                "Используйте /reset для перенастройки."
            )
        elif "permission" in error_message.lower() or "403" in error_message:
            error_text = (
                "❌ Нет доступа к странице.\n\n"
                "Убедитесь, что:\n"
                "• Интеграция добавлена на страницу\n"
                "• У интеграции есть права на редактирование\n\n"
                "Используйте /reset для перенастройки."
            )
        else:
            error_text = (
                f"❌ Ошибка при записи заметки: {error_message}\n\n"
                "Попробуйте еще раз или используйте /reset для перенастройки."
            )
        
        await update.message.reply_text(error_text)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сброс конфигурации пользователя."""
    user_id = update.effective_user.id
    db.reset_user_config(user_id)
    
    await update.message.reply_text(
        "🔄 Конфигурация сброшена. Используйте /start для новой настройки."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущей операции."""
    await update.message.reply_text(
        "❌ Операция отменена. Используйте /start для начала настройки."
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по использованию бота."""
    help_text = (
        "📖 Справка по использованию бота:\n\n"
        "Команды:\n"
        "• /start - Начать настройку бота\n"
        "• /reset - Сбросить текущую конфигурацию\n"
        "• /help - Показать эту справку\n\n"
        "Использование:\n"
        "После настройки просто отправляйте сообщения боту, "
        "и они будут автоматически добавляться в ваш Notion Inbox."
    )
    await update.message.reply_text(help_text)


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
    
    # Регистрируем обработчики
    application.add_handler(setup_handler)
    application.add_handler(CommandHandler('reset', reset))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Инициализируем базу данных
    db.init_database()
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
