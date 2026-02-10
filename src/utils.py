"""Utility functions and keyboard builders.

This module contains helper functions and inline keyboard builders
used across the bot handlers.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


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
