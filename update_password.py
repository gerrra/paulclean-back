#!/usr/bin/env python3
"""
Обновление SMTP пароля в .env файле
"""

import getpass

def update_password():
    """Обновляет SMTP пароль в .env файле"""
    print("🔐 Обновление SMTP пароля")
    print("=" * 40)
    
    print("\n📋 Для Google Workspace нужно:")
    print("1. Включить двухфакторную аутентификацию")
    print("2. Создать App Password")
    print("3. Использовать App Password (16 символов)")
    
    print("\n🔗 Ссылка: https://myaccount.google.com/security")
    print("   Раздел: 'App passwords' (Пароли приложений)")
    
    new_password = getpass.getpass("\nВведите новый App Password: ").strip()
    
    if len(new_password) != 16:
        print("❌ App Password должен быть 16 символов")
        return False
    
    # Обновляем .env файл
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Обновляем пароль
        for i, line in enumerate(lines):
            if line.startswith('SMTP_PASSWORD='):
                lines[i] = f'SMTP_PASSWORD={new_password}\n'
                break
        
        # Записываем обновленный файл
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Пароль обновлен в .env файле!")
        print("\n📝 Теперь можете протестировать SMTP:")
        print("   python3 test_smtp.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении .env: {e}")
        return False

if __name__ == "__main__":
    update_password()
