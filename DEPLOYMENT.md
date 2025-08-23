# 🚀 Инструкция по развертыванию PaulClean Backend

## Подготовка сервера

### 1. Подключение к серверу
```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes root@165.22.43.35
```

### 2. Запуск скрипта развертывания
```bash
# Сделать скрипт исполняемым
chmod +x scripts/deploy.sh

# Запустить развертывание
./scripts/deploy.sh
```

## Настройка переменных окружения

После развертывания отредактируйте файл `.env`:

```bash
nano /opt/paulclean/paulclean-back/.env
```

### Обязательные настройки:
- `DATABASE_URL` - URL базы данных PostgreSQL
- `SECRET_KEY` - секретный ключ для JWT токенов
- `SMTP_*` - настройки SMTP для отправки email
- `CORS_ORIGINS` - разрешенные домены для CORS

## Обновление приложения

Для быстрого обновления используйте:

```bash
chmod +x scripts/update.sh
./scripts/update.sh
```

## Полезные команды

### Проверка статуса
```bash
cd /opt/paulclean/paulclean-back
docker-compose ps
```

### Просмотр логов
```bash
# Логи API
docker-compose logs -f api

# Логи базы данных
docker-compose logs -f postgres

# Логи Redis
docker-compose logs -f redis
```

### Перезапуск сервисов
```bash
docker-compose restart api
docker-compose restart nginx
```

### Проверка Nginx
```bash
nginx -t
systemctl status nginx
```

## Структура проекта на сервере

```
/opt/paulclean/
└── paulclean-back/
    ├── app/                    # Код приложения
    ├── alembic/               # Миграции базы данных
    ├── docker-compose.yml     # Конфигурация Docker
    ├── .env                   # Переменные окружения
    └── scripts/               # Скрипты развертывания
```

## Мониторинг

### Проверка здоровья приложения
```bash
curl http://165.22.43.35/health
```

### Проверка портов
```bash
netstat -tlnp | grep :80
netstat -tlnp | grep :8000
```

## Устранение неполадок

### Если приложение не запускается:
1. Проверьте логи: `docker-compose logs api`
2. Проверьте статус контейнеров: `docker-compose ps`
3. Проверьте переменные окружения в `.env`

### Если Nginx не работает:
1. Проверьте конфигурацию: `nginx -t`
2. Проверьте статус: `systemctl status nginx`
3. Проверьте логи: `tail -f /var/log/nginx/error.log`

### Если база данных недоступна:
1. Проверьте статус PostgreSQL: `docker-compose logs postgres`
2. Проверьте подключение: `docker-compose exec postgres psql -U cleaning_user -d cleaning_service`

## Безопасность

- Firewall настроен автоматически (порты 22, 80, 443)
- Nginx настроен как reverse proxy
- Приложение работает в Docker контейнерах
- Рекомендуется настроить SSL сертификат через Let's Encrypt

## Настройка SSL (опционально)

```bash
certbot --nginx -d your-domain.com
```
