#!/bin/bash

echo "🚀 Обновление сервера..."

# Проверяем подключение к серверу
echo "📡 Проверяем подключение к серверу..."
if ! ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes root@165.22.43.35 "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Сервер недоступен. Попробуйте позже."
    exit 1
fi

echo "✅ Сервер доступен!"

# Загружаем обновленные файлы
echo "📤 Загружаем обновленные файлы на сервер..."
scp -i ~/.ssh/id_ed25519 docker-compose.yml root@165.22.43.35:/opt/fastapi-backend/
scp -i ~/.ssh/id_ed25519 Dockerfile root@165.22.43.35:/opt/fastapi-backend/

# Подключаемся к серверу и обновляем
echo "🔧 Обновляем сервер..."
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes root@165.22.43.35 << 'EOF'
cd /opt/fastapi-backend

echo "📋 Останавливаем контейнеры..."
docker-compose down

echo "🔨 Пересобираем API..."
docker-compose build --no-cache api

echo "🚀 Запускаем контейнеры..."
docker-compose up -d

echo "⏳ Ждем запуска API..."
sleep 30

echo "📊 Проверяем статус..."
docker-compose ps

echo "🧪 Тестируем API..."
curl -s http://localhost:8000/health

echo "🎯 Обновление завершено!"
EOF

echo "✅ Сервер обновлен успешно!"
echo "📬 Теперь можно протестировать отправку email через SendGrid"
