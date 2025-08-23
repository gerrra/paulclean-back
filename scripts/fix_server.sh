#!/bin/bash

echo "=== Исправляем проблемы на сервере ==="

# 1. Останавливаем все контейнеры
echo "1. Останавливаем все контейнеры..."
docker-compose down --remove-orphans

# 2. Удаляем старые образы
echo "2. Удаляем старые образы..."
docker system prune -f

# 3. Создаем резервную копию docker-compose.yml
echo "3. Создаем резервную копию..."
cp docker-compose.yml docker-compose.yml.backup

# 4. Создаем новый docker-compose.yml без nginx
echo "4. Создаем новый docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: cleaning_service_postgres
    environment:
      POSTGRES_DB: cleaning_service
      POSTGRES_USER: cleaning_user
      POSTGRES_PASSWORD: cleaning_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_postgres.sql:/docker-entrypoint-initdb.d/init_postgres.sql
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cleaning_user -d cleaning_service"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - cleaning_service_network

  # Redis for Celery
  redis:
    image: redis:7-alpine
    container_name: cleaning_service_redis
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cleaning_service_network

  # FastAPI Application
  api:
    build: .
    container_name: cleaning_service_api
    environment:
      - DATABASE_URL=postgresql://cleaning_user:cleaning_password@postgres:5432/cleaning_service
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key-change-in-production
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - WORKING_HOURS_START=10:00
      - WORKING_HOURS_END=19:00
      - SLOT_DURATION_MINUTES=30
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
    networks:
      - cleaning_service_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  cleaning_service_network:
    driver: bridge
EOF

# 5. Запускаем контейнеры
echo "5. Запускаем контейнеры..."
docker-compose up -d

# 6. Ждем запуска
echo "6. Ждем запуска сервисов..."
sleep 20

# 7. Проверяем статус
echo "7. Проверяем статус..."
docker-compose ps

# 8. Проверяем логи
echo "8. Проверяем логи API..."
docker-compose logs api --tail=20

echo "=== Исправление завершено ==="
echo "API доступен по адресу: http://165.22.43.35:8000"
echo "Проверить статус: docker-compose ps"
echo "Логи: docker-compose logs -f api"
