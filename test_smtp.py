#!/usr/bin/env python3
"""
Тест SMTP подключения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.email_service import EmailService

def test_smtp():
    """Тестирует SMTP подключение"""
    print("🧪 Тестирование SMTP подключения...")
    print("=" * 50)
    
    # Проверяем настройки
    print("📋 SMTP настройки:")
    print(f"   Сервер: {settings.smtp_server}")
    print(f"   Порт: {settings.smtp_port}")
    print(f"   Пользователь: {settings.smtp_username}")
    print(f"   TLS: {settings.smtp_tls}")
    print(f"   STARTTLS: {settings.smtp_starttls}")
    
    if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password]):
        print("\n❌ SMTP настройки неполные!")
        print("   Проверьте файл .env")
        return False
    
    print("\n✅ SMTP настройки корректны")
    
    # Тестируем отправку email
    test_email = "test@example.com"
    test_url = "http://localhost:8000/verify-email/test-token"
    
    print(f"\n📧 Отправляем тестовый email на {test_email}...")
    print(f"   Ссылка верификации: {test_url}")
    
    try:
        success = EmailService.send_verification_email(
            test_email, test_url, "Test User"
        )
        
        if success:
            print("✅ Тестовый email отправлен успешно!")
            print("\n📝 Теперь можете:")
            print("1. Зарегистрировать нового пользователя")
            print("2. Проверить почту - должно прийти письмо верификации")
            print("3. Перейти по ссылке для подтверждения email")
            print("4. Попробовать залогиниться")
            return True
        else:
            print("❌ Ошибка отправки тестового email")
            print("   Проверьте логи приложения")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании SMTP: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
