# 🛠️ Ручная настройка сервера

## Шаг 1: Подключение к серверу
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes root@165.22.43.35
```

## Шаг 2: Установка Docker Compose
```bash
apt update
apt install -y docker-compose
```

## Шаг 3: Запуск Docker
```bash
systemctl start docker
systemctl enable docker
```

## Шаг 4: Переход в директорию проекта
```bash
cd /opt/fastapi-backend
```

## Шаг 5: Проверка Docker
```bash
docker --version
docker-compose --version
```

## Шаг 6: Остановка существующих контейнеров
```bash
docker-compose down
```

## Шаг 7: Сборка и запуск
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Шаг 8: Проверка статуса
```bash
docker-compose ps
```

## Шаг 9: Просмотр логов (если нужно)
```bash
docker-compose logs -f api
```

## Альтернатива: Выполнение скрипта
Если хотите использовать автоматический скрипт:
```bash
cd /opt/fastapi-backend
chmod +x scripts/setup_server.sh
./scripts/setup_server.sh
```

## Проверка работы приложения
```bash
curl http://localhost:8000/health
curl http://165.22.43.35/health
```

## Полезные команды
- `docker-compose ps` - статус контейнеров
- `docker-compose logs -f api` - логи приложения
- `docker-compose restart api` - перезапуск API
- `docker-compose down && docker-compose up -d` - полный перезапуск
