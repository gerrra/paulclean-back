#!/usr/bin/env python3
"""
Скрипт для тестирования email верификации
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Тестирует регистрацию нового пользователя"""
    print("🔐 Тестирование регистрации...")
    
    data = {
        "full_name": "Email Test User",
        "email": "test-verification@paulcleanwa.com",
        "phone": "+1234567890",
        "address": "Test Address for Email",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/register", json=data)
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Регистрация успешна!")
        print(f"   User ID: {result['user']['id']}")
        print(f"   Email: {result['user']['email']}")
        print(f"   Access Token: {result['access_token'][:20]}...")
        return result
    else:
        print(f"❌ Ошибка регистрации: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_login_without_verification():
    """Тестирует логин без верификации email"""
    print("\n🔑 Тестирование логина без верификации...")
    
    data = {
        "email": "test-verification@paulcleanwa.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/login", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Логин успешен! (Email автоматически верифицирован)")
        print(f"   Access Token: {result['access_token'][:20]}...")
        return result
    else:
        print(f"❌ Ошибка логина: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_verification_endpoint():
    """Тестирует endpoint верификации email"""
    print("\n🔗 Тестирование endpoint верификации...")
    
    # Получаем токен из базы данных (в реальном приложении он приходит в email)
    import sqlite3
    
    try:
        conn = sqlite3.connect('cleaning_service.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT email_verification_token FROM clients WHERE email = ?", 
                      ("test-verification@paulcleanwa.com",))
        result = cursor.fetchone()
        
        if result and result[0]:
            token = result[0]
            print(f"   Найден токен верификации: {token[:20]}...")
            
            # Тестируем GET endpoint
            response = requests.get(f"{BASE_URL}/api/verify-email/{token}")
            
            if response.status_code == 200:
                print("✅ GET endpoint верификации работает!")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Ошибка GET endpoint: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Тестируем POST endpoint
            post_data = {"token": token}
            response = requests.post(f"{BASE_URL}/api/verify-email", json=post_data)
            
            if response.status_code == 200:
                print("✅ POST endpoint верификации работает!")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Ошибка POST endpoint: {response.status_code}")
                print(f"   Response: {response.text}")
                
        else:
            print("⚠️  Токен верификации не найден в базе данных")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")

def check_database_status():
    """Проверяет статус пользователей в базе данных"""
    print("\n📊 Статус базы данных...")
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('cleaning_service.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, email_verified, email_verification_token, 
                   created_at, updated_at 
            FROM clients 
            ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        print("   Пользователи в базе данных:")
        for row in results:
            user_id, email, verified, token, created, updated = row
            status = "✅ Верифицирован" if verified else "❌ Не верифицирован"
            token_info = f"Токен: {token[:20]}..." if token else "Токен: нет"
            print(f"     ID {user_id}: {email} - {status}")
            print(f"           {token_info}")
            print(f"           Создан: {created}")
            print(f"           Обновлен: {updated}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование Email Верификации")
    print("=" * 50)
    
    # Тест 1: Регистрация
    registration_result = test_registration()
    
    if registration_result:
        # Тест 2: Логин
        login_result = test_login_without_verification()
        
        # Тест 3: Endpoint верификации
        test_verification_endpoint()
        
        # Тест 4: Статус базы данных
        check_database_status()
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено!")
    
    print("\n📝 Рекомендации:")
    print("1. Создайте файл .env с SMTP настройками")
    print("2. Отключите автоматическую верификацию в app/api/auth.py")
    print("3. Перезапустите приложение")
    print("4. Протестируйте отправку email")

if __name__ == "__main__":
    main()
