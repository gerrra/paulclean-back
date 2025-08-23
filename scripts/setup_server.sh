#!/bin/bash

echo "=== Настройка сервера для PaulClean Backend ==="

# 1. Установка Docker Compose
echo "1. Устанавливаем Docker Compose..."
apt update
apt install -y docker-compose

# 2. Запуск Docker
echo "2. Запускаем Docker..."
systemctl start docker
systemctl enable docker

# 3. Проверка статуса
echo "3. Проверяем статус Docker..."
docker --version
docker-compose --version

# 4. Переход в директорию проекта
echo "4. Переходим в директорию проекта..."
cd /opt/fastapi-backend

# 5. Остановка существующих контейнеров
echo "5. Останавливаем существующие контейнеры..."
docker-compose down

# 6. Сборка и запуск
echo "6. Собираем и запускаем контейнеры..."
docker-compose build --no-cache
docker-compose up -d

# 7. Проверка статуса
echo "7. Проверяем статус контейнеров..."
sleep 10
docker-compose ps

echo "=== Настройка завершена ==="
echo "Проверьте статус: docker-compose ps"
echo "Логи: docker-compose logs -f api"
