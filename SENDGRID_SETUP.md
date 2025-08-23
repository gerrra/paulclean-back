# Настройка SendGrid для отправки email

## Шаг 1: Получение API ключа SendGrid

1. Зарегистрируйтесь на [SendGrid](https://sendgrid.com/)
2. Перейдите в Settings → API Keys
3. Создайте новый API ключ с правами "Mail Send"
4. Скопируйте API ключ

## Шаг 2: Настройка docker-compose.yml

1. Скопируйте `docker-compose.example.yml` в `docker-compose.yml`
2. Замените `YOUR_SENDGRID_API_KEY_HERE` на ваш реальный API ключ
3. Замените `YOUR_SECRET_KEY_HERE` на случайную строку для SECRET_KEY

## Шаг 3: Запуск приложения

```bash
docker-compose up -d
```

## Шаг 4: Тестирование

Отправьте POST запрос на `/api/register` с валидными данными пользователя.

## Безопасность

⚠️ **ВАЖНО**: Никогда не коммитьте реальные API ключи в git репозиторий!

- Используйте `.env` файлы для локальной разработки
- Используйте переменные окружения на сервере
- Добавьте `*.env` в `.gitignore`
