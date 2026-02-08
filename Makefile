.PHONY: up down update logs restart build rebuild clean status help check-docker install-docker start-docker

# Определяем команду docker compose (поддержка старых и новых версий)
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# Проверка установки и запуска Docker
check-docker:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker не установлен!"; \
		echo ""; \
		echo "📖 Для установки выполните: make install-docker"; \
		exit 1; \
	fi
	@if ! docker info >/dev/null 2>&1; then \
		echo "❌ Docker daemon не запущен!"; \
		echo ""; \
		echo "💡 Для запуска:"; \
		echo "   macOS: make start-docker"; \
		echo "   Linux: sudo systemctl start docker"; \
		exit 1; \
	fi

# Инструкции по установке Docker
install-docker:
	@echo "🐳 Установка Docker:"
	@echo ""
	@echo "📱 macOS:"
	@echo "   brew install --cask docker"
	@echo "   Или скачайте с https://www.docker.com/products/docker-desktop"
	@echo ""
	@echo "🐧 Linux (Ubuntu/Debian):"
	@echo "   curl -fsSL https://get.docker.com | sh"
	@echo "   sudo usermod -aG docker $$USER"
	@echo "   # Перелогинитесь после установки!"
	@echo ""
	@echo "🪟 Windows:"
	@echo "   Скачайте Docker Desktop с https://www.docker.com/products/docker-desktop"
	@echo ""
	@echo "✅ После установки: make start-docker (macOS) или sudo systemctl start docker (Linux)"

# Запуск Docker Desktop (macOS)
start-docker:
	@if [ "$$(uname)" = "Darwin" ]; then \
		open -a Docker; \
		echo "⏳ Ожидание запуска Docker..."; \
		sleep 10; \
		$(MAKE) check-docker; \
	else \
		echo "⚠️  Эта команда только для macOS"; \
		echo "💡 Для Linux используйте: sudo systemctl start docker"; \
	fi

# Запуск контейнера в фоновом режиме
up: check-docker
	@echo "🚀 Запуск бота..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Бот запущен!"
	@echo "📋 Просмотр логов: make logs"

# Остановка и удаление контейнера
down:
	@echo "🛑 Остановка бота..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Бот остановлен"

# Обновление из git + полная пересборка + перезапуск
update: check-docker
	@echo "🔄 Обновление бота..."
	@bash scripts/update.sh || true
	@echo ""
	@echo "🔨 Запуск полной пересборки..."
	$(MAKE) rebuild

# Просмотр логов в реальном времени
logs: check-docker
	@echo "📋 Просмотр логов (Ctrl+C для выхода)..."
	$(DOCKER_COMPOSE) logs -f bot

# Перезапуск без обновления кода
restart: check-docker
	@echo "🔄 Перезапуск бота..."
	$(DOCKER_COMPOSE) restart
	@echo "✅ Бот перезапущен"

# Пересборка Docker образа
build: check-docker
	@echo "🔨 Сборка образа..."
	$(DOCKER_COMPOSE) build --no-cache
	@echo "✅ Образ собран"

# Полная пересборка образа (при добавлении новых файлов)
rebuild: check-docker
	@echo "🔄 Полная пересборка образа..."
	@echo "🛑 Остановка контейнера..."
	$(DOCKER_COMPOSE) down
	@echo "🗑️  Удаление старого образа..."
	-docker rmi $$(docker images -q inbox_bot-bot 2>/dev/null) 2>/dev/null || true
	@echo "🔨 Сборка нового образа..."
	$(DOCKER_COMPOSE) build --no-cache
	@echo "🚀 Запуск контейнера..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Образ пересобран и запущен!"
	@echo "📋 Просмотр логов: make logs"

# Полная очистка
clean: check-docker
	@echo "🧹 Очистка..."
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "✅ Очистка завершена"

# Статус контейнера
status: check-docker
	@$(DOCKER_COMPOSE) ps

# Полное развёртывание
deploy: check-docker
	@echo "🚀 Развёртывание..."
	@bash scripts/deploy.sh

# Справка
help:
	@echo "🤖 Управление ботом:"
	@echo "  make up             - Запуск бота"
	@echo "  make down           - Остановка бота"
	@echo "  make update         - Обновление из git и перезапуск"
	@echo "  make logs           - Просмотр логов"
	@echo "  make restart        - Перезапуск без обновления"
	@echo "  make build          - Пересборка образа"
	@echo "  make rebuild        - Полная пересборка (при новых файлах)"
	@echo "  make clean          - Полная очистка"
	@echo "  make status         - Статус контейнера"
	@echo "  make deploy         - Полное развёртывание"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make install-docker - Инструкции по установке Docker"
	@echo "  make start-docker   - Запуск Docker Desktop (macOS)"
