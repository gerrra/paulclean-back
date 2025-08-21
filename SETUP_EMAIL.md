# Настройка Email для верификации

## Проблема
При регистрации пользователи должны получать письмо с подтверждением email, но SMTP настройки не настроены.

## Решение

### 1. Создайте файл .env в корне проекта:

```bash
# Скопируйте env.example в .env
cp env.example .env
```

### 2. Настройте SMTP в .env файле:

#### Для Gmail:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
SMTP_STARTTLS=true
```

#### Для Yandex:
```env
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=587
SMTP_USERNAME=your-email@yandex.ru
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
SMTP_STARTTLS=true
```

### 3. Как получить App Password для Gmail:

1. Включите двухфакторную аутентификацию в Google Account
2. Перейдите в Security → App passwords
3. Создайте новый пароль для приложения
4. Используйте этот пароль в SMTP_PASSWORD

### 4. Включите верификацию email:

В файле `app/api/auth.py` найдите строку:
```python
# В режиме разработки автоматически верифицируем email
if not client.email_verified:
    client.email_verified = True
    db.commit()
    print(f"⚠️  Auto-verified email for {client.email} in development mode")
```

И замените на:
```python
# Проверяем верификацию email
if not client.email_verified:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Email not verified. Please check your email for verification link."
    )
```

### 5. Перезапустите приложение:

```bash
# Остановите текущий процесс
pkill -f uvicorn

# Запустите заново
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Тестирование

После настройки SMTP:

1. Зарегистрируйте нового пользователя
2. Проверьте почту - должно прийти письмо с ссылкой верификации
3. Перейдите по ссылке для подтверждения email
4. Попробуйте залогиниться

## Текущий статус

✅ Регистрация работает  
✅ Автоматическая верификация email (режим разработки)  
✅ Логин работает  
⚠️  SMTP не настроен  
⚠️  Письма не отправляются  

## Альтернативное решение для разработки

Если вы не хотите настраивать SMTP, можете оставить автоматическую верификацию email для разработки. В этом случае пользователи смогут логиниться сразу после регистрации без подтверждения email.
