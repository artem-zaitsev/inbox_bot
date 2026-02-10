"""Command and message handlers.

This module contains all handler functions for Telegram bot commands,
message processing, and callback queries.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.app_globals import db, notion_client, notification_manager
from src.notion_api import NotionClient
from src.utils import (
    get_time_keyboard,
    get_days_keyboard,
    get_yes_no_keyboard,
    format_days,
    get_notifications_actions_keyboard,
    get_timezone_keyboard,
    gmt_to_offset_seconds,
    offset_seconds_to_gmt,
    local_time_to_utc,
    utc_time_to_local,
)
from src.version import VERSION, is_newer_version, should_show_notifications_intro, get_changelog_message

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_NOTION_TOKEN, WAITING_FOR_PAGE = range(2)
SETTING_NOTIFICATIONS, WAITING_FOR_NOTIFICATION_TIME, WAITING_FOR_NOTIFICATION_DAYS, WAITING_FOR_TIMEZONE = range(3, 7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start с проверкой версии."""
    user_id = update.effective_user.id

    # Проверяем есть ли уже сохраненная конфигурация
    config = db.get_user_config(user_id)

    if config and config.get('notion_token') and config.get('page_id'):
        # Пользователь уже настроен - проверяем версию
        result = await check_and_show_changelog(update, context)
        if result is not None:
            return result

        await update.message.reply_text(
            "✅ Вы уже настроили бота!\n\n"
            "Ваша конфигурация:\n"
            f"• Страница: {config.get('page_name', 'Не указано')}\n\n"
            "Просто отправьте сообщение, и оно будет добавлено в ваш Inbox.\n\n"
            "Используйте /reset для перенастройки."
        )
        return ConversationHandler.END

    # Новый пользователь - устанавливаем текущую версию
    db.set_user_version(user_id, VERSION)

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


async def check_and_show_changelog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверить и показать changelog для новых версий.

    Если версия пользователя < текущей версии:
    - Показываем сообщение текущей версии (CHANGELOG[VERSION]['message'])
    - Если версия < 1.1.0 - это новая функция нотификаций
    - Обновляем версию пользователя
    """
    user_id = update.effective_user.id
    user_version = db.get_user_version(user_id)
    current_version = VERSION

    # Проверяем есть ли новая версия
    if is_newer_version(current_version, user_version):
        logger.info(f"Пользователь {user_id}: версия {user_version} -> {current_version}")

        # Проверяем нужно ли показать intro для нотификаций
        if should_show_notifications_intro(user_version):
            # Это первая версия с нотификациями - показываем специальное сообщение
            await update.message.reply_text(
                "🎉 Новая функция: Оповещения о неразобранном инбоксе!\n\n"
                "Я могу отправлять вам уведомления с неотмеченными задачами "
                "в выбранное время и дни недели.\n\n"
                "Хотите настроить?",
                reply_markup=get_yes_no_keyboard()
            )
            return SETTING_NOTIFICATIONS
        else:
            # Показываем общий changelog
            changelog_msg = get_changelog_message(current_version)
            if changelog_msg:
                await update.message.reply_text(changelog_msg)

        # Обновляем версию пользователя
        db.set_user_version(user_id, current_version)

    return None


async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие настройки уведомлений."""
    user_id = update.effective_user.id
    settings = db.get_notification_settings(user_id)
    
    if not settings.get('notification_enabled'):
        # Если уведомления выключены - показываем кнопки Да/Нет
        await update.message.reply_text(
            "🔕 Уведомления выключены.\n\n"
            "Хотите настроить рассылку о неразобранном инбоксе?",
            reply_markup=get_yes_no_keyboard()
        )
        return SETTING_NOTIFICATIONS
    else:
        # Уведомления включены - показываем текущие настройки
        timezone_offset = settings.get('timezone_offset')
        utc_time = settings.get('notification_time', 'Не установлено')
        
        # Конвертируем UTC время в локальное для отображения
        if timezone_offset and utc_time != 'Не установлено':
            local_time = utc_time_to_local(utc_time, timezone_offset)
            time_display = f"{local_time} ({offset_seconds_to_gmt(timezone_offset)})"
        else:
            time_display = utc_time
        
        await update.message.reply_text(
            f"📬 Настройки уведомлений:\n\n"
            f"Статус: ✅ Включены\n"
            f"Время: {time_display}\n"
            f"Дни: {format_days(settings.get('notification_days', ''))}\n\n"
            f"Хотите изменить настройки?",
            reply_markup=get_notifications_actions_keyboard()
        )
        return SETTING_NOTIFICATIONS


async def handle_notification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка inline-кнопок для уведомлений."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    
    if data == "notif_yes":
        # Проверяем, выбран ли уже часовой пояс
        settings = db.get_notification_settings(user_id)
        if settings.get('timezone_offset') is None:
            # Новый пользователь - сначала выбираем таймзону
            await query.edit_message_text(
                "Выберите ваш часовой пояс:",
                reply_markup=get_timezone_keyboard()
            )
            return WAITING_FOR_TIMEZONE
        else:
            # Таймзона уже выбрана - показываем выбор времени
            await query.edit_message_text(
                "Выберите время для рассылки:",
                reply_markup=get_time_keyboard()
            )
            return WAITING_FOR_NOTIFICATION_TIME
    
    elif data == "notif_no":
        # Отметить что приветствие показано (устанавливаем текущую версию)
        db.set_user_version(user_id, VERSION)
        await query.edit_message_text(
            "Окей! Если передумаете - используйте команду /notifications"
        )
        return ConversationHandler.END
    
    elif data == "notif_change":
        # Проверяем, выбран ли уже часовой пояс
        settings = db.get_notification_settings(user_id)
        if settings.get('timezone_offset') is None:
            # Таймзона не выбрана - сначала выбираем
            await query.edit_message_text(
                "Выберите ваш часовой пояс:",
                reply_markup=get_timezone_keyboard()
            )
            return WAITING_FOR_TIMEZONE
        else:
            # Таймзона уже выбрана - показываем выбор времени
            await query.edit_message_text(
                "Выберите время для рассылки:",
                reply_markup=get_time_keyboard()
            )
            return WAITING_FOR_NOTIFICATION_TIME
    
    elif data == "notif_disable":
        # Отключить уведомления
        db.save_notification_settings(user_id, False, None, None)
        notification_manager.update_user_schedule(user_id, False, None, None)
        await query.edit_message_text(
            "🔕 Уведомления отключены.\n\n"
            "Используйте /notifications чтобы включить снова."
        )
        return ConversationHandler.END
    
    elif data.startswith("tz_"):
        # Сохранить выбранный часовой пояс
        gmt_offset = int(data.replace("tz_", ""))
        timezone_offset = gmt_to_offset_seconds(gmt_offset)
        context.user_data['timezone_offset'] = timezone_offset
        
        await query.edit_message_text(
            f"✅ Выбран часовой пояс: {offset_seconds_to_gmt(timezone_offset)}\n\n"
            "Теперь выберите время для рассылки:",
            reply_markup=get_time_keyboard()
        )
        return WAITING_FOR_NOTIFICATION_TIME
    
    elif data.startswith("time_"):
        # Сохранить время, показать выбор дней
        time = data.replace("time_", "")
        context.user_data['notification_time'] = time
        context.user_data['selected_days'] = ['1', '2', '3', '4', '5']  # По умолчанию пн-пт
        await query.edit_message_text(
            "Выберите дни недели для рассылки:",
            reply_markup=get_days_keyboard(context.user_data['selected_days'])
        )
        return WAITING_FOR_NOTIFICATION_DAYS
    
    elif data.startswith("day_toggle_"):
        # Переключить день, обновить клавиатуру
        day = data.replace("day_toggle_", "")
        selected = context.user_data.get('selected_days', ['1', '2', '3', '4', '5'])
        if day in selected:
            selected.remove(day)
        else:
            selected.append(day)
        context.user_data['selected_days'] = selected
        await query.edit_message_text(
            "Выберите дни недели для рассылки:",
            reply_markup=get_days_keyboard(selected)
        )
        return WAITING_FOR_NOTIFICATION_DAYS
    
    elif data == "days_done":
        # Сохранить все настройки
        local_time = context.user_data.get('notification_time')
        days = ','.join(context.user_data.get('selected_days', ['1', '2', '3', '4', '5']))
        timezone_offset = context.user_data.get('timezone_offset')
        
        # Конвертируем локальное время в UTC
        if timezone_offset:
            utc_time = local_time_to_utc(local_time, timezone_offset)
        else:
            utc_time = local_time  # Для старых пользователей без таймзоны
        
        db.save_notification_settings(user_id, True, utc_time, days, timezone_offset)
        db.set_user_version(user_id, VERSION)
        
        # Запланировать в notification_manager (используем UTC время)
        notif_mgr = context.bot_data.get('notification_manager')
        if notif_mgr:
            notif_mgr.update_user_schedule(user_id, True, utc_time, days)
        
        # Для отображения используем локальное время
        time_display = f"{local_time} ({offset_seconds_to_gmt(timezone_offset)})" if timezone_offset else local_time
        
        await query.edit_message_text(
            f"✅ Уведомления настроены!\n\n"
            f"⏰ Время: {time_display}\n"
            f"📅 Дни: {format_days(days)}\n\n"
            f"Я буду присылать список неотмеченных задач по расписанию.\n"
            f"Используйте /notifications для изменения настроек."
        )
        return ConversationHandler.END
    
    return ConversationHandler.END


async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список заметок из Notion."""
    user_id = update.effective_user.id
    
    # Проверяем конфигурацию
    config = db.get_user_config(user_id)
    if not config or not config.get('notion_token') or not config.get('page_id'):
        await update.message.reply_text(
            "⚠️ Бот не настроен. Используйте /start для начала настройки."
        )
        return
    
    try:
        # Устанавливаем токен
        notion_client.set_token(config['notion_token'])
        
        # Получаем заметки
        notes = notion_client.get_page_content(config['page_id'], limit=20)
        
        if not notes:
            await update.message.reply_text("📭 Заметок пока нет")
            return
        
        # Форматируем вывод
        lines = [f"📋 Ваши последние заметки ({len(notes)}):\n"]
        
        for text, is_checked in notes:
            if is_checked is True:
                checkbox = "☑"
            elif is_checked is False:
                checkbox = "☐"
            else:
                checkbox = "•"  # Для paragraph
            lines.append(f"{checkbox} {text}")
        
        message = "\n".join(lines)
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении заметок: {str(e)}\n\n"
            "Попробуйте позже или используйте /reset для перенастройки."
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
        "• /list - Показать последние 20 заметок\n"
        "• /notifications - Настроить уведомления о неразобранном инбоксе\n"
        "• /reset - Сбросить текущую конфигурацию\n"
        "• /help - Показать эту справку\n\n"
        "Использование:\n"
        "После настройки просто отправляйте сообщения боту, "
        "и они будут автоматически добавляться в ваш Notion Inbox."
    )
    await update.message.reply_text(help_text)


async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую версию бота."""
    await update.message.reply_text(f"📦 Версия бота: {VERSION}")
