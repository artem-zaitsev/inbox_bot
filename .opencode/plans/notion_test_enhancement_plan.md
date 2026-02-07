# План: Доработка теста Notion API

## Цель
Доработать тест `test_notion_get_user_data` чтобы:
1. Логировать весь сырой ответ от API
2. Проверять что имя пользователя равно "Artem"

## Задачи

### 1. Добавить логирование
**Файл:** `tests/test_notion_api.py`
**Изменения:**
- Добавить импорт `logging`
- Настроить логгер
- Добавить `logger.info()` с выводом всего `user_data`
- Использовать `json.dumps()` для красивого форматирования JSON

### 2. Добавить проверку имени
**Файл:** `tests/test_notion_api.py`
**Изменения:**
- Добавить assert: `user_data.get("name") == "Artem"`
- Добавить понятное сообщение об ошибке если имя не совпадает

## Итоговый код теста

```python
"""
Тесты для проверки работы с Notion API.
"""

import os
import json
import logging
import pytest
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    Тест пройдёт успешно, если API отвечает без ошибок и имя пользователя "Artem".
    """
    client = get_notion_client()
    
    # Пытаемся получить данные пользователя
    user_data = client.client.users.me()
    
    # Логируем весь сырой ответ от API
    logger.info(f"Notion API Response:\n{json.dumps(user_data, indent=2, ensure_ascii=False)}")
    
    # Проверяем что получили ответ (не None)
    assert user_data is not None, "Не удалось получить данные пользователя"
    
    # Проверяем что имя пользователя равно "Artem"
    user_name = user_data.get("name")
    assert user_name == "Artem", f"Ожидалось имя 'Artem', получено: '{user_name}'"
```

## Как использовать после реализации

```bash
# Установить зависимости (если ещё не установлены)
pip install -r requirements.txt

# Создать/отредактировать .env файл
echo "NOTION_TEST_TOKEN=secret_..." > .env

# Запустить тест
pytest tests/test_notion_api.py -v -s
```

## Ожидаемый результат

При успешном прохождении теста:
1. В консоли будет выведен JSON с данными пользователя
2. Тест проверит что поле `name` равно "Artem"
3. Если имя не совпадёт - тест упадёт с понятным сообщением

## Проверка

Тест будет:
- ✅ Пропускаться если `NOTION_TEST_TOKEN` не найден
- ✅ Логировать весь JSON ответ от API
- ✅ Проверять что `name == "Artem"`
- ❌ Падать если имя не "Artem"
