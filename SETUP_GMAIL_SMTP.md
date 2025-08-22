# Настройка Gmail SMTP для отправки email

## 🔧 Шаги настройки:

### 1. Включить 2FA в Gmail
1. Перейдите в [Google Account Settings](https://myaccount.google.com/)
2. Выберите "Security" (Безопасность)
3. Включите "2-Step Verification" (Двухэтапная аутентификация)

### 2. Создать App Password
1. В том же разделе "Security" найдите "App passwords" (Пароли приложений)
2. Нажмите "Create" (Создать)
3. Выберите "Mail" и "Other (Custom name)"
4. Введите название: "Cleaning Service API"
5. Скопируйте сгенерированный пароль (16 символов)

### 3. Обновить env.local
Замените в файле `env.local`:

```ini
SMTP_USERNAME=your-real-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

**Пример:**
```ini
SMTP_USERNAME=bogzaschita@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

### 4. Перезапустить сервер
После обновления `env.local` перезапустите API сервер.

## ⚠️ Важные моменты:

- **НЕ используйте** обычный пароль от Gmail
- **Используйте только** App Password
- **App Password** генерируется только при включенной 2FA
- **Пароль** должен быть ровно 16 символов (без пробелов)

## 🧪 Тестирование:

После настройки протестируйте отправку email:
```bash
curl -X POST "http://localhost:8000/api/resend-verification-email" \
  -H "Content-Type: application/json" \
  -d '{"email": "bogzaschita@gmail.com"}'
```

## 🔒 Безопасность:

- `env.local` уже добавлен в `.gitignore`
- App Password можно отозвать в любой момент
- Каждый App Password уникален для конкретного приложения
