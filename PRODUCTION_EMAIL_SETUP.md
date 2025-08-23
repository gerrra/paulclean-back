# 📧 Настройка продакшн email для PaulClean

## 🎯 Проблема
Сервер не может отправлять email через внешние SMTP серверы из-за блокировки провайдером.

## 🚀 Решения

### Вариант 1: SendGrid (Рекомендуется)
1. **Зарегистрируйтесь на [SendGrid](https://sendgrid.com/)**
2. **Получите API ключ** в разделе Settings → API Keys
3. **Обновите docker-compose.yml:**
   ```yaml
   environment:
     - SMTP_SERVER=smtp.sendgrid.net
     - SMTP_PORT=587
     - SMTP_USERNAME=apikey
     - SMTP_PASSWORD=SG.YOUR_ACTUAL_API_KEY_HERE
     - SMTP_TLS=true
     - SMTP_STARTTLS=true
   ```

### Вариант 2: Mailgun
1. **Зарегистрируйтесь на [Mailgun](https://mailgun.com/)**
2. **Получите SMTP credentials**
3. **Обновите docker-compose.yml:**
   ```yaml
   environment:
     - SMTP_SERVER=smtp.mailgun.org
     - SMTP_PORT=587
     - SMTP_USERNAME=postmaster@yourdomain.mailgun.org
     - SMTP_PASSWORD=YOUR_ACTUAL_PASSWORD
     - SMTP_TLS=true
     - SMTP_STARTTLS=true
   ```

### Вариант 3: AWS SES
1. **Настройте [AWS SES](https://aws.amazon.com/ses/)**
2. **Получите SMTP credentials**
3. **Обновите docker-compose.yml:**
   ```yaml
   environment:
     - SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
     - SMTP_PORT=587
     - SMTP_USERNAME=YOUR_SES_USERNAME
     - SMTP_PASSWORD=YOUR_SES_PASSWORD
     - SMTP_TLS=true
     - SMTP_STARTTLS=true
   ```

## 🔧 Настройка DNS для улучшения доставляемости

### SPF Record
Добавьте в DNS вашего домена:
```
paulcleanwa.com. IN TXT "v=spf1 include:_spf.google.com ~all"
```

### DKIM Record
Настройте DKIM через выбранный email сервис.

### DMARC Record
Добавьте в DNS:
```
_dmarc.paulcleanwa.com. IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@paulcleanwa.com"
```

## 📝 Пошаговая настройка

1. **Выберите email сервис** (рекомендую SendGrid)
2. **Получите credentials** от выбранного сервиса
3. **Обновите docker-compose.yml** с правильными настройками
4. **Перезапустите API:**
   ```bash
   cd /opt/fastapi-backend
   docker-compose down
   docker-compose up -d
   ```
5. **Протестируйте отправку:**
   ```bash
   curl -X POST 'http://localhost:8000/api/register' \
     -H 'Content-Type: application/json' \
     -d '{"full_name":"Test User","email":"bogzaschita@icloud.com","phone":"+1234567890","address":"Test Address","password":"testpass123"}'
   ```

## 🧪 Тестирование

После настройки проверьте:
1. **Логи API** - должно быть `✅ Verification email sent to...`
2. **Почту** - письмо должно прийти
3. **Спам-папку** - иногда письма попадают туда

## ⚠️ Важные моменты

- **Не используйте Gmail** - заблокировано провайдером
- **SendGrid** часто работает лучше всего
- **Настройте DNS записи** для улучшения доставляемости
- **Мониторьте логи** для диагностики проблем

## 🔍 Диагностика

Если email не работает:
```bash
# Проверьте логи API
docker-compose logs api | grep -i email

# Проверьте статус контейнеров
docker-compose ps

# Проверьте health check
curl http://localhost:8000/health
```

## 📞 Поддержка

При проблемах:
1. Проверьте логи
2. Убедитесь, что credentials правильные
3. Проверьте DNS настройки
4. Обратитесь к документации выбранного email сервиса
