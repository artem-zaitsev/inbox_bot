#!/bin/bash

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

echo -e "${BLUE}🚀 Начало развёртывания...${NC}"
echo -e "${BLUE}🐳 Используется команда: ${DOCKER_COMPOSE}${NC}"
echo ""

# Проверка наличия .env
if [ ! -f .env ]; then
    if [ -f example.env ]; then
        echo -e "${YELLOW}⚠️  Файл .env не найден, копируем из example.env...${NC}"
        cp example.env .env
        echo -e "${GREEN}✅ Файл .env создан${NC}"
        echo -e "${YELLOW}⚠️  ВАЖНО: Отредактируйте .env и укажите реальные значения!${NC}"
        echo ""
        read -p "Продолжить развёртывание? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Развёртывание отменено${NC}"
            exit 0
        fi
    else
        echo -e "${RED}❌ Файлы .env и example.env не найдены!${NC}"
        exit 1
    fi
fi

# Проверка Docker
echo -e "${YELLOW}🔍 Проверка Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker найден${NC}"

# Остановка старых контейнеров
echo ""
echo -e "${YELLOW}🛑 Остановка старых контейнеров...${NC}"
$DOCKER_COMPOSE down 2>/dev/null || true

# Удаление старых образов (опционально)
echo ""
echo -e "${YELLOW}🧹 Очистка старых образов...${NC}"
$DOCKER_COMPOSE rm -f 2>/dev/null || true

# Сборка нового образа
echo ""
echo -e "${YELLOW}🔨 Сборка Docker образа...${NC}"
$DOCKER_COMPOSE build --no-cache

echo -e "${GREEN}✅ Образ собран${NC}"

# Создание директории для данных если её нет
if [ ! -d data ]; then
    echo ""
    echo -e "${YELLOW}📁 Создание директории для данных...${NC}"
    mkdir -p data
    echo -e "${GREEN}✅ Директория data создана${NC}"
fi

# Запуск контейнера
echo ""
echo -e "${YELLOW}🚀 Запуск контейнера...${NC}"
$DOCKER_COMPOSE up -d

echo -e "${GREEN}✅ Контейнер запущен${NC}"

# Проверка статуса
echo ""
echo -e "${YELLOW}⏳ Проверка статуса (ожидание 5 сек)...${NC}"
sleep 5

if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo ""
    echo -e "${GREEN}✅ Бот успешно развёрнут и работает!${NC}"
    echo ""
    echo -e "${BLUE}📊 Информация о контейнере:${NC}"
    $DOCKER_COMPOSE ps
    echo ""
    echo -e "${BLUE}📋 Первые логи:${NC}"
    $DOCKER_COMPOSE logs --tail=20 bot
    echo ""
    echo -e "${GREEN}🎉 Развёртывание завершено успешно!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Полезные команды:${NC}"
    echo "   make logs     - Просмотр логов"
    echo "   make down     - Остановка бота"
    echo "   make update   - Обновление из git"
    echo "   make status   - Статус контейнера"
else
    echo ""
    echo -e "${RED}❌ Контейнер не запустился!${NC}"
    echo -e "${YELLOW}📋 Логи ошибок:${NC}"
    $DOCKER_COMPOSE logs bot
    exit 1
fi
