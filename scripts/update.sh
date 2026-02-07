#!/bin/bash

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Определяем команду docker compose (поддержка старых и новых версий)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}❌ Docker Compose не найден!${NC}"
    echo -e "${YELLOW}💡 Установите Docker Compose:${NC}"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${YELLOW}🔄 Начало обновления...${NC}"
echo -e "${YELLOW}🐳 Используется команда: ${DOCKER_COMPOSE}${NC}"

# Проверка наличия .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}💡 Скопируйте example.env в .env и настройте переменные:${NC}"
    echo "   cp example.env .env"
    exit 1
fi

# Проверка, что мы в git репозитории
if [ ! -d .git ]; then
    echo -e "${RED}❌ Git репозиторий не найден!${NC}"
    exit 1
fi

# Сохраняем текущий хеш коммита
OLD_COMMIT=$(git rev-parse HEAD)
echo -e "${YELLOW}📍 Текущий коммит: ${OLD_COMMIT:0:7}${NC}"

# Получаем изменения из git
echo -e "${YELLOW}📥 Получение изменений из git...${NC}"
git fetch origin

# Проверяем, есть ли изменения
if git diff --quiet HEAD origin/main 2>/dev/null || git diff --quiet HEAD origin/master 2>/dev/null; then
    echo -e "${GREEN}✅ Код актуален, изменений нет${NC}"
else
    echo -e "${YELLOW}📦 Обнаружены изменения, обновляем...${NC}"
    
    # Определяем основную ветку (main или master)
    BRANCH=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's/origin\///' || echo "main")
    
    # Pull изменений
    git pull origin $BRANCH
    
    echo -e "${GREEN}✅ Код обновлён${NC}"
    
    # Пересобираем образ
    echo -e "${YELLOW}🔨 Пересборка Docker образа...${NC}"
    $DOCKER_COMPOSE build --no-cache
    
    echo -e "${GREEN}✅ Образ пересобран${NC}"
fi

# Перезапускаем контейнер
echo -e "${YELLOW}🔄 Перезапуск контейнера...${NC}"
$DOCKER_COMPOSE down
$DOCKER_COMPOSE up -d

# Проверяем статус
echo -e "${YELLOW}⏳ Ожидание запуска...${NC}"
sleep 3

if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Бот успешно запущен!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Статус контейнера:${NC}"
    $DOCKER_COMPOSE ps
    echo ""
    echo -e "${YELLOW}📋 Логи (последние 10 строк):${NC}"
    $DOCKER_COMPOSE logs --tail=10 bot
    echo ""
    echo -e "${GREEN}💡 Для просмотра логов в реальном времени: make logs${NC}"
else
    echo -e "${RED}❌ Ошибка запуска контейнера!${NC}"
    echo -e "${YELLOW}📋 Логи ошибок:${NC}"
    $DOCKER_COMPOSE logs bot
    exit 1
fi
