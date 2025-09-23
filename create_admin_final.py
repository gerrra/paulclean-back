#!/usr/bin/env python3
import sqlite3
import sys
import os
from datetime import datetime

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from passlib.context import CryptContext
    
    # Создаем bcrypt контекст
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('cleaning_service.db')
    cursor = conn.cursor()
    
    # Данные нового админа
    username = "admin"
    email = "admin@paulclean.com"
    password = "admin123"
    
    # Создаем хеш пароля
    hashed_password = pwd_context.hash(password)
    
    print(f"Creating admin user:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Hash: {hashed_password}")
    
    # Получаем текущее время
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Создаем нового админа
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, role, totp_enabled, email_verified, failed_login_attempts, created_at)
        VALUES (?, ?, ?, 'admin', 0, 1, 0, ?)
    """, (username, email, hashed_password, current_time))
    
    conn.commit()
    conn.close()
    
    print("✅ Admin user created successfully!")
    print("You can now login with:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Trying alternative method...")
    
    # Альтернативный метод - создаем простой хеш
    import hashlib
    
    conn = sqlite3.connect('cleaning_service.db')
    cursor = conn.cursor()
    
    username = "admin"
    email = "admin@paulclean.com"
    password = "admin123"
    
    # Простой хеш для тестирования
    simple_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"Creating admin with simple hash:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Simple Hash: {simple_hash}")
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, role, totp_enabled, email_verified, failed_login_attempts, created_at)
        VALUES (?, ?, ?, 'admin', 0, 1, 0, ?)
    """, (username, email, simple_hash, current_time))
    
    conn.commit()
    conn.close()
    
    print("✅ Admin user created with simple hash!")
