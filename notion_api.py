"""
Модуль для работы с Notion API.
"""

import re
import logging
from typing import Optional, Tuple

try:
    from notion_client import Client
except ImportError:
    raise ImportError(
        "Пакет 'notion-client' не установлен. "
        "Установите его командой: pip install notion-client"
    )

logger = logging.getLogger(__name__)


class NotionClient:
    """Класс для работы с Notion API."""
    
    def __init__(self, token: Optional[str] = None):
        """Инициализация клиента Notion."""
        self.token = token
        self.client = None
        if token:
            self.set_token(token)
    
    def set_token(self, token: str):
        """Установить токен и создать клиент."""
        self.token = token
        self.client = Client(auth=token)
    
    def test_connection(self):
        """Проверить соединение с Notion API."""
        if not self.client:
            raise ValueError("Токен не установлен")
        
        try:
            # Пробуем получить список пользователей
            self.client.users.me()
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {e}")
            raise Exception(f"Не удалось подключиться к Notion: {str(e)}")
    
    def extract_page_id_from_url(self, url: str) -> Optional[str]:
        """Извлечь ID страницы из URL Notion."""
        # Формат URL: https://www.notion.so/Page-Name-{page_id}
        # или https://{workspace}.notion.site/Page-Name-{page_id}
        
        # Ищем UUID в формате с дефисами (36 символов)
        pattern_with_dashes = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern_with_dashes, url, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Ищем UUID без дефисов (32 символа) в конце URL
        parts = url.split('?')[0].split('/')
        if parts:
            last_part = parts[-1]
            
            # Если последняя часть длиннее 32 символов, ищем ID в конце
            if len(last_part) >= 32:
                # Пробуем найти 32 hex символа в конце
                hex_pattern = r'([a-f0-9]{32})$'
                hex_match = re.search(hex_pattern, last_part, re.IGNORECASE)
                
                if hex_match:
                    # Конвертируем в формат с дефисами
                    hex_id = hex_match.group(1)
                    formatted_id = f"{hex_id[:8]}-{hex_id[8:12]}-{hex_id[12:16]}-{hex_id[16:20]}-{hex_id[20:]}"
                    return formatted_id
                
                # Пробуем найти UUID с дефисами в конце (36 символов)
                uuid_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
                uuid_match = re.search(uuid_pattern, last_part, re.IGNORECASE)
                if uuid_match:
                    return uuid_match.group(1)
        
        return None
    
    def find_page_by_name(self, page_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Найти страницу по названию."""
        if not self.client:
            raise ValueError("Токен не установлен")
        
        try:
            # Ищем страницы в рабочей области пользователя
            search_results = self.client.search(
                query=page_name,
                filter={
                    "property": "object",
                    "value": "page"
                }
            )
            
            results = search_results.get('results', [])
            
            if not results:
                raise ValueError(f"Страница '{page_name}' не найдена")
            
            # Берем первую найденную страницу
            page = results[0]
            page_id = page['id']
            
            # Получаем название страницы
            title = self._get_page_title(page)
            
            return page_id, title
            
        except Exception as e:
            logger.error(f"Ошибка при поиске страницы: {e}")
            raise
    
    def get_page_info(self, page_id: str) -> dict:
        """Получить информацию о странице."""
        if not self.client:
            raise ValueError("Токен не установлен")
        
        try:
            page = self.client.pages.retrieve(page_id)
            title = self._get_page_title(page)
            
            return {
                'id': page_id,
                'title': title,
                'url': page.get('url', '')
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о странице: {e}")
            raise Exception(f"Не удалось получить информацию о странице: {str(e)}")
    
    def _get_page_title(self, page: dict) -> str:
        """Извлечь название страницы из объекта страницы."""
        properties = page.get('properties', {})
        
        # Ищем свойство title
        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get('type')
            if prop_type == 'title':
                title_array = prop_value.get('title', [])
                if title_array:
                    return title_array[0].get('plain_text', 'Без названия')
        
        # Если не нашли title, пробуем получить из URL
        url = page.get('url', '')
        if url:
            # Извлекаем название из URL
            parts = url.split('/')
            if parts:
                last_part = parts[-1]
                # Убираем ID страницы
                title_part = last_part.split('-')[:-1]
                if title_part:
                    return ' '.join(title_part)
        
        return 'Без названия'
    
    def append_to_page(self, page_id: str, content: str):
        """Добавить контент на страницу Notion."""
        if not self.client:
            raise ValueError("Токен не установлен")
        
        try:
            # Получаем информацию о странице
            page = self.client.pages.retrieve(page_id)
            
            # Получаем ID дочерних блоков страницы
            children = self.client.blocks.children.list(page_id)
            
            # Создаем новый блок с текстом (чекбокс)
            new_block = {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ],
                    "checked": False
                }
            }
            
            # Добавляем блок на страницу
            self.client.blocks.children.append(page_id, children=[new_block])
            
            logger.info(f"Контент добавлен на страницу {page_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении контента: {e}")
            error_msg = str(e)
            
            # Более понятные сообщения об ошибках
            if "unauthorized" in error_msg.lower() or "401" in error_msg:
                raise Exception("Ошибка авторизации. Проверьте токен.")
            elif "not found" in error_msg.lower() or "404" in error_msg:
                raise Exception("Страница не найдена. Проверьте ID страницы.")
            elif "permission" in error_msg.lower() or "403" in error_msg:
                raise Exception("Нет доступа к странице. Убедитесь, что интеграция добавлена на страницу.")
            else:
                raise Exception(f"Ошибка при записи в Notion: {error_msg}")
