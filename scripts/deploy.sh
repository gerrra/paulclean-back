#!/bin/bash

# Ручной деплой на сервер

set -e

SERVER_HOST="165.22.43.35"
SERVER_USER="root"
DEPLOY_PATH="/opt/fastapi-backend"
SSH_KEY="~/.ssh/id_ed25519"

echo "🚀 Запуск ручного деплоя..."

# Создаем резервную копию
echo "💾 Создание резервной копии..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST << 'EOF'
  cd /opt/fastapi-backend
  BACKUP_DIR="/opt/backups/manual_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$BACKUP_DIR"
  
  if [ -f "data/cleaning_service_stable.db" ]; then
    cp data/cleaning_service_stable.db "$BACKUP_DIR/"
    echo "✅ Резервная копия создана: $BACKUP_DIR"
  fi
EOF

# Копируем файлы
echo "📁 Копирование файлов..."
rsync -avz --delete -e "ssh -i $SSH_KEY" \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='data/' \
  ./ $SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/

# Выполняем деплой
echo "🔧 Выполнение деплоя на сервере..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST << 'EOF'
  cd /opt/fastapi-backend
  
  # Останавливаем сервисы
  echo "⏹️  Остановка сервисов..."
  docker-compose -f docker-compose.stable.yml down
  
  # Запускаем новые сервисы
  echo "▶️  Запуск новых сервисов..."
  docker-compose -f docker-compose.stable.yml up -d --build
  
  # Ждем запуска
  echo "⏳ Ожидание запуска сервисов..."
  sleep 30
  
  # Проверяем статус
  echo "📊 Статус контейнеров:"
  docker-compose -f docker-compose.stable.yml ps
  
  # Проверяем здоровье API
  echo "🏥 Проверка здоровья API..."
  for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
      echo "✅ API здоров!"
      break
    fi
    echo "⏳ Ожидание API... ($i/10)"
    sleep 10
  done
  
  if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API не отвечает!"
    exit 1
  fi
EOF

echo "🎉 Деплой завершен успешно!"
echo "🌐 API доступен по адресу: http://$SERVER_HOST:8000"
echo "📚 Документация: http://$SERVER_HOST:8000/docs"
