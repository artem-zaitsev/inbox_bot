"""
Модуль для управления уведомлениями о неразобранном инбоксе.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from src.database import Database
from src.notion_api import NotionClient

logger = logging.getLogger(__name__)


class NotificationManager:
    """Менеджер для управления рассылкой уведомлений."""

    def __init__(self, db: Database, notion_client: NotionClient, bot: Bot):
        """Инициализация менеджера уведомлений."""
        self.db = db
        self.notion = notion_client
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}  # user_id -> job_id

    def start(self):
        """Запустить планировщик и загрузить все задачи."""
        self.scheduler.start()
        users = self.db.get_users_with_notifications()
        for user in users:
            self.schedule_user(
                user['user_id'],
                user['notification_time'],
                user['notification_days']
            )
        logger.info(f"Запущено {len(users)} уведомлений")

    def schedule_user(self, user_id: int, time: str, days: str):
        """Запланировать рассылку для конкретного пользователя."""
        try:
            hour, minute = map(int, time.split(':'))
            day_of_week = self._convert_days_to_cron(days)

            job = self.scheduler.add_job(
                self.send_notification,
                CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                args=[user_id],
                id=f"user_{user_id}",
                replace_existing=True
            )
            self.jobs[user_id] = job.id
            logger.info(f"Запланирована рассылка для пользователя {user_id}: {time} в {days}")
        except Exception as e:
            logger.error(f"Ошибка при планировании уведомления для {user_id}: {e}")

    def unschedule_user(self, user_id: int):
        """Удалить запланированную задачу пользователя."""
        if user_id in self.jobs:
            try:
                self.scheduler.remove_job(self.jobs[user_id])
                del self.jobs[user_id]
                logger.info(f"Удалена рассылка для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при удалении уведомления для {user_id}: {e}")

    def update_user_schedule(self, user_id: int, enabled: bool, time: str, days: str):
        """Обновить расписание пользователя."""
        self.unschedule_user(user_id)
        if enabled:
            self.schedule_user(user_id, time, days)

    def _convert_days_to_cron(self, days_str: str) -> str:
        """Конвертировать дни недели в формат cron."""
        days_map = {
            '1': 'mon', '2': 'tue', '3': 'wed', '4': 'thu',
            '5': 'fri', '6': 'sat', '7': 'sun'
        }
        days_list = days_str.split(',')
        return ','.join([days_map[d] for d in days_list if d in days_map])

    async def send_notification(self, user_id: int):
        """Отправить уведомление пользователю."""
        try:
            # Получаем конфигурацию пользователя
            config = self.db.get_user_config(user_id)
            if not config or not config.get('notion_token') or not config.get('page_id'):
                logger.warning(f"Нет конфигурации для пользователя {user_id}")
                return

            # Устанавливаем токен Notion
            self.notion.set_token(config['notion_token'])

            # Получаем все to_do блоки со страницы
            blocks = self.notion.client.blocks.children.list(config['page_id'])
            results = blocks.get('results', [])

            # Фильтруем только невыполненные to_do
            unchecked_items = []
            for block in results:
                if block.get('type') == 'to_do':
                    todo_data = block.get('to_do', {})
                    if not todo_data.get('checked', False):
                        text = self._extract_text(todo_data.get('rich_text', []))
                        if text:
                            unchecked_items.append(text)

            # Формируем сообщение
            if not unchecked_items:
                message = "🎉 Ваш инбокс пуст! Вы молодец!"
            else:
                lines = [f"📬 Неразобранный инбокс ({len(unchecked_items)} задачи):\n"]
                for item in unchecked_items:
                    lines.append(f"☐ {item}")
                lines.append("\n💡 Используйте /list для просмотра всех заметок")
                message = "\n".join(lines)

            # Отправляем сообщение
            await self.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Отправлено уведомление пользователю {user_id}")

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

    def _extract_text(self, rich_text: list) -> str:
        """Извлечь текст из rich_text массива."""
        text_parts = []
        for item in rich_text:
            if item.get('type') == 'text':
                text_parts.append(item.get('text', {}).get('content', ''))
        return ''.join(text_parts)

    def shutdown(self):
        """Остановить планировщик."""
        self.scheduler.shutdown()
        logger.info("Планировщик уведомлений остановлен")
