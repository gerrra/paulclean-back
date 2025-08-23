#!/bin/bash

# Скрипт быстрого обновления PaulClean Backend
set -e

echo "🔄 Обновляем PaulClean Backend..."

cd /opt/paulclean/paulclean-back

# Останавливаем контейнеры
echo "⏹️ Останавливаем контейнеры..."
docker-compose down

# Обновляем код
echo "📥 Обновляем код..."
git pull origin main

# Пересобираем и запускаем
echo "🏗️ Пересобираем и запускаем..."
docker-compose build --no-cache
docker-compose up -d

# Ждем запуска
echo "⏳ Ждем запуска сервисов..."
sleep 20

# Проверяем статус
echo "🔍 Проверяем статус..."
docker-compose ps

echo "✅ Обновление завершено!"
echo "🌐 Приложение доступно по адресу: http://165.22.43.35"
