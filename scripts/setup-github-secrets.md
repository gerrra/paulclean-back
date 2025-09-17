# Настройка GitHub Secrets для автодеплоя

## Необходимые секреты

Для работы автодеплоя нужно добавить следующие секреты в GitHub репозиторий:

### 1. SERVER_SSH_KEY

**Что это:** Приватный SSH ключ для доступа к серверу

**Как получить:**
```bash
# Если у вас уже есть SSH ключ
cat ~/.ssh/id_ed25519

# Или создать новый
ssh-keygen -t ed25519 -C "github-actions@paulclean.com"
```

**Как добавить в GitHub:**
1. Перейдите в репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Name: `SERVER_SSH_KEY`
5. Value: содержимое приватного ключа (начинается с `-----BEGIN OPENSSH PRIVATE KEY-----`)

### 2. SERVER_HOST

**Что это:** IP адрес или домен сервера

**Как добавить в GitHub:**
1. Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `SERVER_HOST`
4. Value: `165.22.43.35`

### 3. SERVER_USER

**Что это:** Имя пользователя для подключения к серверу

**Как добавить в GitHub:**
1. Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `SERVER_USER`
4. Value: `root`

### 4. DEPLOY_PATH

**Что это:** Путь к директории приложения на сервере

**Как добавить в GitHub:**
1. Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `DEPLOY_PATH`
4. Value: `/opt/fastapi-backend`

### 5. Настройка публичного ключа на сервере

```bash
# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@165.22.43.35

# Или вручную добавить в authorized_keys
ssh root@165.22.43.35
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI..." >> ~/.ssh/authorized_keys
```

## Дополнительные секреты (опционально)

### SMTP_PASSWORD
Для отправки уведомлений о деплое
```
Name: SMTP_PASSWORD
Value: ваш-smtp-пароль
```

### SLACK_WEBHOOK_URL
Для уведомлений в Slack
```
Name: SLACK_WEBHOOK_URL
Value: https://hooks.slack.com/services/...
```

## Проверка настройки

После добавления секретов:

1. Сделайте коммит и пуш в main ветку
2. Перейдите в GitHub → Actions
3. Проверьте, что workflow запустился
4. Следите за логами выполнения

## Безопасность

⚠️ **Важно:**
- Никогда не коммитьте SSH ключи в репозиторий
- Используйте отдельный SSH ключ для CI/CD
- Регулярно ротируйте ключи
- Ограничьте права SSH ключа на сервере
