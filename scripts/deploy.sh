#!/bin/bash

# Скрипт развертывания PaulClean Backend на сервере
set -e

echo "🚀 Начинаем развертывание PaulClean Backend..."

# Обновляем систему
echo "📦 Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "🔧 Устанавливаем необходимые пакеты..."
apt install -y \
    docker.io \
    docker-compose \
    git \
    curl \
    wget \
    unzip \
    nginx \
    certbot \
    python3-certbot-nginx

# Запускаем и включаем Docker
echo "🐳 Настраиваем Docker..."
systemctl start docker
systemctl enable docker

# Создаем директорию для проекта
echo "📁 Создаем директорию проекта..."
mkdir -p /opt/paulclean
cd /opt/paulclean

# Клонируем репозиторий (если еще не клонирован)
if [ ! -d "paulclean-back" ]; then
    echo "📥 Клонируем репозиторий..."
    git clone https://github.com/your-username/paulclean-back.git
    cd paulclean-back
else
    echo "📂 Репозиторий уже существует, обновляем..."
    cd paulclean-back
    git pull origin main
fi

# Создаем .env файл из примера
echo "⚙️ Настраиваем переменные окружения..."
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "📝 Файл .env создан из env.example"
    echo "⚠️ Не забудьте отредактировать .env файл с правильными значениями!"
fi

# Строим и запускаем контейнеры
echo "🏗️ Строим и запускаем контейнеры..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Ждем запуска сервисов
echo "⏳ Ждем запуска сервисов..."
sleep 30

# Проверяем статус
echo "🔍 Проверяем статус сервисов..."
docker-compose ps

# Настраиваем Nginx
echo "🌐 Настраиваем Nginx..."
cat > /etc/nginx/sites-available/paulclean << 'EOF'
server {
    listen 80;
    server_name 165.22.43.35;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
    }
}
EOF

# Активируем сайт
ln -sf /etc/nginx/sites-available/paulclean /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию Nginx
nginx -t

# Перезапускаем Nginx
systemctl restart nginx
systemctl enable nginx

# Настраиваем firewall
echo "🔥 Настраиваем firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "✅ Развертывание завершено!"
echo "🌐 Приложение доступно по адресу: http://165.22.43.35"
echo "📊 Статус контейнеров: docker-compose ps"
echo "📝 Логи приложения: docker-compose logs -f api"
echo "🔧 Для редактирования .env: nano /opt/paulclean/paulclean-back/.env"
