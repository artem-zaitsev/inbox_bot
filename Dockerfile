# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
# В данный момент системные зависимости не требуются, но оставляем для будущего использования
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY bot.py database.py notion_api.py notifications.py version.py ./

# Создаем директорию для базы данных (если нужно)
RUN mkdir -p /app/data

# Устанавливаем переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCKER_ENV=true
ENV DATA_DIR=/app/data

# Запускаем бота
CMD ["python", "bot.py"]
