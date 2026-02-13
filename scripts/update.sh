#!/bin/bash

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Начало обновления из git...${NC}"

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
    exit 0
else
    echo -e "${YELLOW}📦 Обнаружены изменения, обновляем...${NC}"
    
    # Определяем основную ветку (main или master)
    BRANCH=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's/origin\///' || echo "main")
    
    # Pull изменений
    git pull origin $BRANCH
    
    echo -e "${GREEN}✅ Код обновлён из git${NC}"
    echo -e "${YELLOW}🔨 Docker-операции будут выполнены через Makefile${NC}"
    exit 0
fi
