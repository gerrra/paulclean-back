#!/usr/bin/env python3
"""
Скрипт для настройки SMTP в .env файле
"""

import os
import getpass

def setup_smtp():
    """Настраивает SMTP в .env файле"""
    print("🚀 Настройка SMTP для отправки email верификации")
    print("=" * 60)
    
    # Проверяем существование .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("   Создайте его командой: cp env.example .env")
        return False
    
    print("📧 Выберите провайдера email:")
    print("1. Gmail (рекомендуется для тестирования)")
    print("2. iCloud")
    print("3. Yandex")
    print("4. Другой (настройка вручную)")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        return setup_gmail()
    elif choice == "2":
        return setup_icloud()
    elif choice == "3":
        return setup_yandex()
    elif choice == "4":
        return setup_custom()
    else:
        print("❌ Неверный выбор")
        return False

def setup_gmail():
    """Настраивает Gmail SMTP"""
    print("\n📧 Настройка Gmail SMTP")
    print("-" * 30)
    
    print("\n📋 Для Gmail и Google Workspace нужно:")
    print("1. Включить двухфакторную аутентификацию")
    print("2. Создать App Password")
    print("3. Использовать App Password вместо обычного пароля")
    
    email = input("\nВведите ваш email адрес: ").strip()
    if not email or '@' not in email:
        print("❌ Неверный email адрес")
        return False
    
    print("\n🔐 Введите App Password (16 символов):")
    print("   Получить можно в Google Account → Security → App passwords")
    password = getpass.getpass("App Password: ").strip()
    
    if len(password) != 16:
        print("❌ App Password должен быть 16 символов")
        return False
    
    # Обновляем .env файл
    update_env_file({
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': password,
        'SMTP_TLS': 'true',
        'SMTP_STARTTLS': 'true'
    })
    
    print("✅ Gmail SMTP настроен!")
    return True

def setup_icloud():
    """Настраивает iCloud SMTP"""
    print("\n📧 Настройка iCloud SMTP")
    print("-" * 30)
    
    print("\n📋 Для iCloud нужно:")
    print("1. Включить двухфакторную аутентификацию")
    print("2. Создать App-Specific Password")
    print("3. Использовать App-Specific Password вместо обычного пароля")
    
    email = input("\nВведите ваш iCloud адрес: ").strip()
    if not email or '@icloud.com' not in email:
        print("❌ Неверный iCloud адрес")
        return False
    
    print("\n🔐 Введите App-Specific Password:")
    print("   Получить можно в Apple ID → Sign-in and Security → App-Specific Passwords")
    password = getpass.getpass("App-Specific Password: ").strip()
    
    if not password:
        print("❌ Пароль не может быть пустым")
        return False
    
    # Обновляем .env файл
    update_env_file({
        'SMTP_SERVER': 'smtp.mail.me.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': password,
        'SMTP_TLS': 'true',
        'SMTP_STARTTLS': 'true'
    })
    
    print("✅ iCloud SMTP настроен!")
    return True

def setup_yandex():
    """Настраивает Yandex SMTP"""
    print("\n📧 Настройка Yandex SMTP")
    print("-" * 30)
    
    email = input("\nВведите ваш Yandex адрес: ").strip()
    if not email or '@yandex.ru' not in email:
        print("❌ Неверный Yandex адрес")
        return False
    
    print("\n🔐 Введите пароль от почты:")
    password = getpass.getpass("Пароль: ").strip()
    
    if not password:
        print("❌ Пароль не может быть пустым")
        return False
    
    # Обновляем .env файл
    update_env_file({
        'SMTP_SERVER': 'smtp.yandex.ru',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': password,
        'SMTP_TLS': 'true',
        'SMTP_STARTTLS': 'true'
    })
    
    print("✅ Yandex SMTP настроен!")
    return True

def setup_custom():
    """Настраивает кастомный SMTP"""
    print("\n📧 Настройка кастомного SMTP")
    print("-" * 30)
    
    server = input("SMTP сервер (например, smtp.example.com): ").strip()
    port = input("Порт (по умолчанию 587): ").strip() or "587"
    username = input("Email адрес: ").strip()
    password = getpass.getpass("Пароль: ").strip()
    
    if not all([server, username, password]):
        print("❌ Не все поля заполнены")
        return False
    
    # Обновляем .env файл
    update_env_file({
        'SMTP_SERVER': server,
        'SMTP_PORT': port,
        'SMTP_USERNAME': username,
        'SMTP_PASSWORD': password,
        'SMTP_TLS': 'true',
        'SMTP_STARTTLS': 'true'
    })
    
    print("✅ Кастомный SMTP настроен!")
    return True

def update_env_file(settings):
    """Обновляет .env файл с новыми настройками SMTP"""
    try:
        # Читаем текущий .env файл
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Обновляем настройки
        for i, line in enumerate(lines):
            for key, value in settings.items():
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    break
        
        # Записываем обновленный файл
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ Файл .env обновлен")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении .env: {e}")
        return False
    
    return True

def test_smtp():
    """Тестирует SMTP подключение"""
    print("\n🧪 Тестирование SMTP подключения...")
    
    try:
        from app.config import settings
        from app.email_service import EmailService
        
        if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password]):
            print("❌ SMTP настройки неполные")
            return False
        
        print(f"   Сервер: {settings.smtp_server}:{settings.smtp_port}")
        print(f"   Пользователь: {settings.smtp_username}")
        print(f"   TLS: {settings.smtp_tls}")
        print(f"   STARTTLS: {settings.smtp_starttls}")
        
        # Тестируем отправку email
        test_email = "test@example.com"
        test_url = "http://localhost:8000/verify-email/test-token"
        
        print(f"\n📧 Отправляем тестовый email на {test_email}...")
        
        success = EmailService.send_verification_email(
            test_email, test_url, "Test User"
        )
        
        if success:
            print("✅ Тестовый email отправлен успешно!")
            return True
        else:
            print("❌ Ошибка отправки тестового email")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании SMTP: {e}")
        return False

def main():
    """Основная функция"""
    print("🔧 Настройка SMTP для Cleaning Service API")
    print("=" * 60)
    
    # Настраиваем SMTP
    if setup_smtp():
        print("\n🎉 SMTP настроен успешно!")
        
        # Спрашиваем о тестировании
        test = input("\n🧪 Протестировать SMTP подключение? (y/n): ").strip().lower()
        if test in ['y', 'yes', 'да']:
            test_smtp()
        
        print("\n📝 Следующие шаги:")
        print("1. Перезапустите приложение")
        print("2. Зарегистрируйте нового пользователя")
        print("3. Проверьте почту - должно прийти письмо верификации")
        print("4. Перейдите по ссылке для подтверждения email")
        print("5. Попробуйте залогиниться")
        
    else:
        print("\n❌ Настройка SMTP не завершена")
        print("   Проверьте настройки и попробуйте снова")

if __name__ == "__main__":
    main()
