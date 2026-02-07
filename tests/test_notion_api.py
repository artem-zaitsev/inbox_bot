"""
Тесты для проверки работы с Notion API.
"""

import os
import json
import pytest
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


def get_notion_client():
    """Получить клиент Notion с токеном из .env файла или переменной окружения."""
    from notion_api import NotionClient
    
    token = os.getenv("NOTION_TEST_TOKEN")
    if not token:
        raise ValueError("NOTION_TEST_TOKEN не найден в .env файле или переменных окружения")
    
    return NotionClient(token)


@pytest.mark.skipif(
    not os.getenv("NOTION_TEST_TOKEN"),
    reason="NOTION_TEST_TOKEN не найден в .env файле - тест пропущен"
)
def test_notion_get_user_data():
    """
    Тест проверяет работоспособность подключения к Notion API.
    
    Использует NOTION_TEST_TOKEN из .env файла (или переменной окружения).
    Тест пройдёт успешно, если API отвечает без ошибок и имя пользователя "inbox writer".
    """
    client = get_notion_client()
    
    # Пытаемся получить данные пользователя
    user_data = client.client.users.me()
    
    # Выводим весь сырой ответ от API
    print(f"\n{'='*60}")
    print("Notion API Response:")
    print(f"{'='*60}")
    print(json.dumps(user_data, indent=2, ensure_ascii=False))
    print(f"{'='*60}")
    
    # Проверяем что получили ответ (не None)
    assert user_data is not None, "Не удалось получить данные пользователя"
    
    # Проверяем что имя пользователя равно "inbox writer"
    user_name = user_data.get("name")
    assert user_name == "inbox writer", f"Ожидалось имя 'inbox writer', получено: '{user_name}'"
