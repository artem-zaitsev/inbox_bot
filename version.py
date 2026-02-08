"""Версия бота и changelog."""

VERSION = "1.1.0"

CHANGELOG = {
    "1.1.0": {
        "features": [
            "📬 Система уведомлений о неразобранном инбоксе",
            "⏰ Настройка времени и дней рассылки уведомлений",
            "🔔 Команда /notifications для управления уведомлениями"
        ],
        "message": (
            "🎉 Новое в версии 1.1.0:\n\n"
            "📬 Уведомления о неразобранном инбоксе!\n\n"
            "Теперь я могу присылать вам напоминания о неотмеченных задачах "
            "в выбранное время. Используйте /notifications чтобы настроить."
        )
    },
    "1.0.0": {
        "features": ["🚀 Первый релиз"],
        "message": "👋 Добро пожаловать в бота для Notion Inbox!"
    }
}


def parse_version(version_str: str) -> tuple:
    """Парсить строку версии в tuple (major, minor, patch)."""
    parts = version_str.split('.')
    return tuple(int(x) for x in parts)


def is_newer_version(current: str, user_version: str) -> bool:
    """Проверить что current версия новее user_version."""
    return parse_version(current) > parse_version(user_version)


def should_show_notifications_intro(user_version: str) -> bool:
    """Проверить нужно ли показать intro для нотификаций (появились в 1.1.0)."""
    return parse_version(user_version) < parse_version("1.1.0")


def get_changelog_message(version: str) -> str:
    """Получить сообщение changelog для версии."""
    return CHANGELOG.get(version, {}).get('message', '')
