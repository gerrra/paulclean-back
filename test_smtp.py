#!/usr/bin/env python3
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """Тестируем подключение к Gmail SMTP"""
    try:
        # Пробуем разные порты и настройки
        print("🔍 Тестируем Gmail SMTP...")
        
        # Тест 1: Порт 587 с STARTTLS
        try:
            print("  📧 Тест 1: Порт 587 с STARTTLS")
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
            server.starttls(context=ssl.create_default_context())
            print("  ✅ Порт 587 доступен!")
            server.quit()
            return True
        except Exception as e:
            print(f"  ❌ Порт 587 недоступен: {e}")
        
        # Тест 2: Порт 465 с SSL
        try:
            print("  📧 Тест 2: Порт 465 с SSL")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
            print("  ✅ Порт 465 доступен!")
            server.quit()
            return True
        except Exception as e:
            print(f"  ❌ Порт 465 недоступен: {e}")
        
        # Тест 3: Порт 25 (стандартный)
        try:
            print("  📧 Тест 3: Порт 25 (стандартный)")
            server = smtplib.SMTP('smtp.gmail.com', 25, timeout=10)
            print("  ✅ Порт 25 доступен!")
            server.quit()
            return True
        except Exception as e:
            print(f"  ❌ Порт 25 недоступен: {e}")
            
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

def test_alternative_smtp():
    """Тестируем альтернативные SMTP серверы"""
    alternatives = [
        ('smtp.mailgun.org', 587),
        ('smtp.sendgrid.net', 587),
        ('smtp.office365.com', 587),
        ('smtp.zoho.com', 587),
        ('smtp.yandex.ru', 587),
    ]
    
    print("\n🔍 Тестируем альтернативные SMTP серверы...")
    
    for host, port in alternatives:
        try:
            print(f"  📧 Тестируем {host}:{port}")
            server = smtplib.SMTP(host, port, timeout=10)
            print(f"  ✅ {host}:{port} доступен!")
            server.quit()
            return host, port
        except Exception as e:
            print(f"  ❌ {host}:{port} недоступен: {e}")
    
    return None, None

def test_local_smtp():
    """Тестируем локальный SMTP"""
    try:
        print("\n🔍 Тестируем локальный SMTP...")
        
        # Пробуем подключиться к localhost
        server = smtplib.SMTP('localhost', 25, timeout=5)
        print("  ✅ Локальный SMTP доступен на порту 25!")
        server.quit()
        return True
    except Exception as e:
        print(f"  ❌ Локальный SMTP недоступен: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Начинаем тестирование SMTP подключений...\n")
    
    # Тест Gmail
    gmail_works = test_gmail_smtp()
    
    # Тест альтернатив
    alt_host, alt_port = test_alternative_smtp()
    
    # Тест локального
    local_works = test_local_smtp()
    
    print("\n📊 Результаты тестирования:")
    print(f"  Gmail SMTP: {'✅ Работает' if gmail_works else '❌ Не работает'}")
    print(f"  Альтернативный SMTP: {'✅ ' + alt_host if alt_host else '❌ Не найден'}")
    print(f"  Локальный SMTP: {'✅ Работает' if local_works else '❌ Не работает'}")
    
    if gmail_works:
        print("\n🎉 Gmail SMTP работает! Можно использовать для отправки email.")
    elif alt_host:
        print(f"\n🎉 Альтернативный SMTP {alt_host} работает! Можно настроить для отправки email.")
    elif local_works:
        print("\n🎉 Локальный SMTP работает! Можно настроить для отправки email.")
    else:
        print("\n❌ Все SMTP серверы недоступны. Нужно искать другие решения.")
