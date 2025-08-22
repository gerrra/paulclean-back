#!/usr/bin/env python3
"""
Тест реальной регистрации с email верификацией
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_real_registration():
    """Тестирует реальную регистрацию с email верификацией"""
    print("🚀 Тест реальной регистрации с email верификацией")
    print("=" * 60)
    
    # Регистрируем нового пользователя
    data = {
        "full_name": "Real Test User",
        "email": "another-test@paulcleanwa.com",
        "phone": "+1234567890",
        "address": "Real Test Address",
        "password": "testpass123"
    }
    
    print(f"📝 Регистрируем пользователя {data['email']}...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/register", json=data)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Регистрация успешна!")
            print(f"   User ID: {result['user']['id']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Access Token: {result['access_token'][:20]}...")
            
            # Проверяем, верифицирован ли email
            if result['user'].get('email_verified'):
                print("⚠️  Email автоматически верифицирован (возможно, SMTP не работает)")
            else:
                print("✅ Email НЕ верифицирован - ожидается верификация")
            
            return result
            
        elif response.status_code == 409:
            print("⚠️  Пользователь уже существует")
            print("   Попробуем залогиниться...")
            return test_login()
            
        else:
            print(f"❌ Ошибка регистрации: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при регистрации: {e}")
        return None

def test_login():
    """Тестирует логин существующего пользователя"""
    print("\n🔑 Тестируем логин...")
    
    data = {
        "email": "bogzaschita@gmail.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/login", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Логин успешен!")
            print(f"   Access Token: {result['access_token'][:20]}...")
            return result
        else:
            print(f"❌ Ошибка логина: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при логине: {e}")
        return None

def check_user_status():
    """Проверяет статус пользователя в базе данных"""
    print("\n📊 Проверяем статус пользователя...")
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('cleaning_service.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, email_verified, email_verification_token, 
                   created_at, updated_at
            FROM clients 
            WHERE email = ?
        """, ("another-test@paulcleanwa.com",))
        
        result = cursor.fetchone()
        
        if result:
            user_id, email, email_verified, token, created_at, updated_at = result
            print(f"   ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Верифицирован: {'✅ Да' if email_verified else '❌ Нет'}")
            print(f"   Токен верификации: {token[:20] + '...' if token else 'Нет'}")
            print(f"   Создан: {created_at}")
            print(f"   Обновлен: {updated_at}")
            
            if token and not email_verified:
                print(f"\n🔗 Ссылка для верификации:")
                print(f"   {BASE_URL}/api/verify-email/{token}")
                
        else:
            print("   Пользователь не найден в базе данных")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование реальной регистрации с email верификацией")
    print("=" * 70)
    
    # Тестируем регистрацию
    result = test_real_registration()
    
    if result:
        # Проверяем статус пользователя
        check_user_status()
        
        print("\n📝 Следующие шаги:")
        print("1. Проверьте почту bogzaschita@gmail.com")
        print("2. Найдите письмо верификации от PaulClean")
        print("3. Перейдите по ссылке для подтверждения email")
        print("4. Попробуйте залогиниться снова")
        
    else:
        print("\n❌ Тест не прошел")
    
    print("\n🏁 Тестирование завершено!")

if __name__ == "__main__":
    main()
