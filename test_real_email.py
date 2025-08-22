#!/usr/bin/env python3
"""
Тест реальной отправки email
"""

import os
import sys
sys.path.append('.')

from app.email_service import EmailService
from app.config import settings

def test_real_email():
    """Тестирует реальную отправку email"""
    print("🧪 Тест реальной отправки email")
    print("=" * 50)
    
    # Проверяем настройки SMTP
    print(f"🔧 SMTP настройки:")
    print(f"   Сервер: {settings.smtp_server}")
    print(f"   Порт: {settings.smtp_port}")
    print(f"   Пользователь: {settings.smtp_username}")
    print(f"   Пароль: {'*' * len(settings.smtp_password) if settings.smtp_password else 'НЕ НАСТРОЕН'}")
    print(f"   TLS: {settings.smtp_tls}")
    print(f"   STARTTLS: {settings.smtp_starttls}")
    print()
    
    # Тестируем отправку простого email
    test_email = "bogzaschita@gmail.com"  # Отправляем на ваш реальный email
    subject = "Тест Email Верификации - PaulClean"
    
    html_content = """
    <html>
    <body>
        <h2>Тест Email Верификации</h2>
        <p>Это тестовое письмо для проверки работы SMTP.</p>
        <p>Если вы получили это письмо, значит SMTP настроен правильно!</p>
        <hr>
        <p><small>Отправлено с PaulClean API</small></p>
    </body>
    </html>
    """
    
    text_content = """
    Тест Email Верификации
    
    Это тестовое письмо для проверки работы SMTP.
    Если вы получили это письмо, значит SMTP настроен правильно!
    
    Отправлено с PaulClean API
    """
    
    print(f"📧 Отправляем тестовый email на {test_email}...")
    
    try:
        result = EmailService.send_email(test_email, subject, html_content, text_content)
        
        if result:
            print("✅ Email отправлен успешно!")
            print("📝 Проверьте почту test@example.com")
        else:
            print("❌ Email не отправлен")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке email: {e}")
    
    print()
    
    # Тестируем отправку email верификации
    print("🔐 Тестируем отправку email верификации...")
    
    verification_url = "http://localhost:8000/verify-email/test-token-123"
    user_name = "Test User"
    
    try:
        result = EmailService.send_verification_email(
            test_email, verification_url, user_name
        )
        
        if result:
            print("✅ Email верификации отправлен успешно!")
            print("📝 Проверьте почту test@example.com")
        else:
            print("❌ Email верификации не отправлен")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке email верификации: {e}")

if __name__ == "__main__":
    test_real_email()
