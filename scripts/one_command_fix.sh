#!/bin/bash

echo "=== Исправляем сервер одной командой ==="

cd /opt/fastapi-backend

# Останавливаем все
docker-compose down --remove-orphans

# Создаем новый docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    container_name: cleaning_service_postgres
    environment:
      POSTGRES_DB: cleaning_service
      POSTGRES_USER: cleaning_user
      POSTGRES_PASSWORD: cleaning_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    networks:
      - cleaning_service_network
  redis:
    image: redis:7-alpine
    container_name: cleaning_service_redis
    ports:
      - "6380:6379"
    networks:
      - cleaning_service_network
  api:
    build: .
    container_name: cleaning_service_api
    environment:
      - DATABASE_URL=postgresql://cleaning_user:cleaning_password@postgres:5432/cleaning_service
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key-change-in-production
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./app:/app/app
    networks:
      - cleaning_service_network
volumes:
  postgres_data:
networks:
  cleaning_service_network:
    driver: bridge
EOF

# Запускаем
docker-compose up -d

# Проверяем
sleep 10
docker-compose ps

echo "=== Готово! API на порту 8000 ==="
