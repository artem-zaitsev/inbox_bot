# Инструкция по запуску в Docker

## Быстрый старт

### 1. Подготовка

Создайте файл `.env` в корне проекта:
```bash
echo "TELEGRAM_BOT_TOKEN=ваш_токен_бота" > .env
```

### 2. Запуск через Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 3. Запуск через Docker напрямую

```bash
# Сборка образа
docker build -t inbox-bot .

# Запуск контейнера
docker run -d \
  --name inbox_bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="ваш_токен_бота" \
  -v $(pwd)/data:/app/data \
  inbox-bot

# Просмотр логов
docker logs -f inbox_bot

# Остановка
docker stop inbox_bot
docker rm inbox_bot
```

## Структура данных

- База данных сохраняется в директории `./data` на хосте
- Данные сохраняются между перезапусками контейнера благодаря volume mount

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` - токен Telegram бота (обязательно)
- `DATA_DIR` - директория для базы данных (по умолчанию: `/app/data`)
- `DOCKER_ENV` - флаг Docker окружения (устанавливается автоматически)

## Обновление бота

```bash
# Остановите контейнер
docker-compose down

# Пересоберите образ
docker-compose build --no-cache

# Запустите снова
docker-compose up -d
```

## Отладка

```bash
# Запуск в интерактивном режиме
docker-compose run --rm bot /bin/bash

# Просмотр логов за последние 100 строк
docker-compose logs --tail=100

# Перезапуск контейнера
docker-compose restart
```
