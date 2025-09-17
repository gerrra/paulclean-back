#!/bin/bash

# Скрипт для тестирования деплоя локально

set -e

SERVER_HOST="165.22.43.35"
SERVER_USER="root"
DEPLOY_PATH="/opt/fastapi-backend"
SSH_KEY="~/.ssh/id_ed25519"

echo "🚀 Тестирование деплоя на сервер..."

# Проверяем SSH соединение
echo "📡 Проверка SSH соединения..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST "echo '✅ SSH соединение работает'"

# Проверяем текущий статус сервера
echo "📊 Текущий статус сервера..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST << 'EOF'
  cd /opt/fastapi-backend
  echo "=== Docker контейнеры ==="
  docker-compose -f docker-compose.stable.yml ps
  echo ""
  echo "=== Дисковое пространство ==="
  df -h /opt/fastapi-backend
  echo ""
  echo "=== API здоровье ==="
  curl -f http://localhost:8000/health || echo "❌ API недоступен"
EOF

# Тестируем копирование файлов
echo "📁 Тестирование копирования файлов..."
rsync -avz --dry-run -e "ssh -i $SSH_KEY" \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='data/' \
  ./ $SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/

echo "✅ Тест завершен успешно!"
echo ""
echo "Для запуска реального деплоя используйте:"
echo "  ./scripts/deploy.sh"
