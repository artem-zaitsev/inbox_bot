"""Utility functions and keyboard builders.

This module contains helper functions and inline keyboard builders
used across the bot handlers.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_timezone_keyboard():
    """Клавиатура с выбором часового пояса (GMT-12 до GMT+14)."""
    keyboard = []
    # Создаем список GMT от -12 до +14
    gmt_values = list(range(-12, 15))  # -12, -11, ..., 0, ..., 14
    
    # По 5 кнопок в ряд
    for i in range(0, len(gmt_values), 5):
        row = []
        for offset in gmt_values[i:i+5]:
            if offset >= 0:
                label = f"GMT+{offset}"
            else:
                label = f"GMT{offset}"
            row.append(InlineKeyboardButton(label, callback_data=f"tz_{offset}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


def gmt_to_offset_seconds(gmt_offset: int) -> int:
    """Конвертировать GMT offset в секунды.
    
    Args:
        gmt_offset: Например, 3 для GMT+3, -5 для GMT-5
        
    Returns:
        Смещение в секундах
    """
    return gmt_offset * 3600


def offset_seconds_to_gmt(offset_seconds: int) -> str:
    """Конвертировать смещение в секундах в строку GMT.
    
    Args:
        offset_seconds: Смещение в секундах
        
    Returns:
        Строка типа "GMT+3" или "GMT-5"
    """
    if offset_seconds is None:
        return "UTC"
    hours = offset_seconds // 3600
    if hours >= 0:
        return f"GMT+{hours}"
    else:
        return f"GMT{hours}"


def local_time_to_utc(time_str: str, timezone_offset: int) -> str:
    """Конвертировать локальное время в UTC.
    
    Args:
        time_str: Время в формате "HH:MM"
        timezone_offset: Смещение в секундах (например, 10800 для GMT+3)
        
    Returns:
        Время в UTC в формате "HH:MM"
    """
    hour, minute = map(int, time_str.split(':'))
    offset_hours = timezone_offset // 3600
    utc_hour = (hour - offset_hours) % 24
    return f"{utc_hour:02d}:{minute:02d}"


def utc_time_to_local(time_str: str, timezone_offset: int) -> str:
    """Конвертировать UTC время в локальное.
    
    Args:
        time_str: Время в формате "HH:MM" (UTC)
        timezone_offset: Смещение в секундах (например, 10800 для GMT+3)
        
    Returns:
        Локальное время в формате "HH:MM"
    """
    hour, minute = map(int, time_str.split(':'))
    offset_hours = timezone_offset // 3600
    local_hour = (hour + offset_hours) % 24
    return f"{local_hour:02d}:{minute:02d}"


def get_time_keyboard():
    """Клавиатура с выбором времени (07:00-22:00, шаг 1 час)."""
    keyboard = []
    times = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00",
             "13:00", "14:00", "15:00", "16:00", "17:00", "18:00",
             "19:00", "20:00", "21:00", "22:00"]
    # По 4 кнопки в ряд
    for i in range(0, len(times), 4):
        row = [InlineKeyboardButton(t, callback_data=f"time_{t}") for t in times[i:i+4]]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_days_keyboard(selected_days=None):
    """Клавиатура с выбором дней недели (множественный выбор)."""
    if selected_days is None:
        selected_days = ['1', '2', '3', '4', '5']  # По умолчанию пн-пт
    
    days = [("Пн", "1"), ("Вт", "2"), ("Ср", "3"), ("Чт", "4"), 
            ("Пт", "5"), ("Сб", "6"), ("Вс", "7")]
    
    keyboard = []
    for name, value in days:
        prefix = "✅ " if value in selected_days else "☐ "
        keyboard.append([InlineKeyboardButton(f"{prefix}{name}", 
                                            callback_data=f"day_toggle_{value}")])
    
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="days_done")])
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard():
    """Клавиатура Да/Нет."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да", callback_data="notif_yes"),
         InlineKeyboardButton("Нет, спасибо", callback_data="notif_no")]
    ])


def format_days(days_str):
    """Форматировать дни недели для отображения."""
    if not days_str:
        return "Не выбраны"
    days_map = {
        '1': 'Пн', '2': 'Вт', '3': 'Ср', '4': 'Чт',
        '5': 'Пт', '6': 'Сб', '7': 'Вс'
    }
    days_list = days_str.split(',')
    result = []
    for d in days_list:
        day_name = days_map.get(d)
        if day_name:
            result.append(day_name)
    return ', '.join(result)


def get_notifications_actions_keyboard():
    """Клавиатура действий для уведомлений."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Изменить", callback_data="notif_change"),
         InlineKeyboardButton("🔕 Отключить", callback_data="notif_disable")]
    ])
