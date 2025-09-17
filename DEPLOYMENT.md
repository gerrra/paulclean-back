# 🚀 Автодеплой на сервер

## Обзор

Настроен автоматический деплой на продакшн сервер при пуше в main ветку через GitHub Actions.

## Файлы деплоя

- `.github/workflows/deploy.yml` - Простой workflow для деплоя
- `.github/workflows/deploy-advanced.yml` - Продвинутый workflow с тестами и откатом
- `scripts/test-deploy.sh` - Тестирование деплоя локально
- `scripts/deploy.sh` - Ручной деплой
- `scripts/setup-github-secrets.md` - Инструкции по настройке секретов

## Быстрая настройка

### 1. Добавить секреты в GitHub

**Необходимые секреты:**
- `SERVER_SSH_KEY` - приватный SSH ключ
- `SERVER_HOST` - IP сервера (165.22.43.35)
- `SERVER_USER` - пользователь (root)
- `DEPLOY_PATH` - путь деплоя (/opt/fastapi-backend)

```bash
# Получить приватный ключ
cat ~/.ssh/id_ed25519

# Добавить в GitHub:
# Settings → Secrets and variables → Actions → New repository secret
# Name: SERVER_SSH_KEY
# Value: [содержимое приватного ключа]
```

### 2. Настроить публичный ключ на сервере

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@165.22.43.35
```

### 3. Проверить настройку

```bash
./scripts/test-deploy.sh
```

## Использование

### Автоматический деплой
- Просто сделайте `git push` в main ветку
- GitHub Actions автоматически запустит деплой
- Следите за прогрессом в GitHub → Actions

### Ручной деплой
```bash
./scripts/deploy.sh
```

### Ручной запуск через GitHub
- Перейдите в GitHub → Actions
- Выберите workflow "Advanced Deploy"
- Нажмите "Run workflow"

## Что происходит при деплое

1. **Тестирование** (опционально) - запуск pytest
2. **Резервное копирование** - создание backup базы данных
3. **Копирование файлов** - синхронизация кода с сервером
4. **Перезапуск сервисов** - остановка старых, запуск новых контейнеров
5. **Проверка здоровья** - тестирование API
6. **Откат при ошибке** - автоматическое восстановление

## Мониторинг

### Проверка статуса
```bash
# SSH на сервер
ssh root@165.22.43.35

# Проверка контейнеров
docker-compose -f /opt/fastapi-backend/docker-compose.stable.yml ps

# Проверка логов
docker-compose -f /opt/fastapi-backend/docker-compose.stable.yml logs -f

# Проверка API
curl http://localhost:8000/health
```

### Внешняя проверка
- API: http://165.22.43.35:8000/health
- Документация: http://165.22.43.35:8000/docs

## Безопасность

- ✅ SSH ключи хранятся в GitHub Secrets
- ✅ Автоматическое резервное копирование
- ✅ Откат при ошибках
- ✅ Проверка здоровья API
- ✅ Логирование всех операций

## Устранение неполадок

### Проблема: SSH ключ не работает
```bash
# Проверить права на ключ
chmod 600 ~/.ssh/id_ed25519

# Проверить соединение
ssh -i ~/.ssh/id_ed25519 root@165.22.43.35
```

### Проблема: Контейнеры не запускаются
```bash
# SSH на сервер и проверить логи
ssh root@165.22.43.35
cd /opt/fastapi-backend
docker-compose -f docker-compose.stable.yml logs
```

### Проблема: API не отвечает
```bash
# Проверить порты
netstat -tlnp | grep 8000

# Проверить контейнеры
docker ps
```

## Дополнительные возможности

### Уведомления в Slack
Добавьте секрет `SLACK_WEBHOOK_URL` для уведомлений о деплое.

### Email уведомления
Добавьте секреты `SMTP_*` для отправки email уведомлений.

### Мониторинг производительности
Интеграция с Prometheus/Grafana для мониторинга метрик.
