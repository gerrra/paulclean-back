#!/bin/bash

echo "Загружаем файлы на сервер..."

# Копируем модифицированный docker-compose.yml
scp -i ~/.ssh/id_ed25519 docker-compose.modified.yml root@165.22.43.35:/opt/fastapi-backend/docker-compose.yml

# Копируем обновленные скрипты
scp -i ~/.ssh/id_ed25519 scripts/setup_server.sh root@165.22.43.35:/opt/fastapi-backend/scripts/
scp -i ~/.ssh/id_ed25519 scripts/update.sh root@165.22.43.35:/opt/fastapi-backend/scripts/

echo "Файлы загружены!"
echo "Теперь на сервере выполните:"
echo "cd /opt/fastapi-backend"
echo "chmod +x scripts/*.sh"
echo "docker-compose up -d"
