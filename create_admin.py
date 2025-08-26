#!/usr/bin/env python3
import sqlite3
import hashlib
import os

# Подключаемся к базе данных
conn = sqlite3.connect('cleaning_service.db')
cursor = conn.cursor()

# Новые данные админа
username = "admin"
email = "admin@cleaningservice.com"
password = "admin123"  # Простой пароль для тестирования

# Создаем хеш пароля (bcrypt-подобный)
salt = os.urandom(16)
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
# Формат: $2b$12$ + salt + hash (имитируем bcrypt формат)
bcrypt_like_hash = f"$2b$12${salt.hex()[:22]}{password_hash.hex()[:31]}"

print(f"Creating admin user:")
print(f"Username: {username}")
print(f"Email: {email}")
print(f"Password: {password}")
print(f"Hash: {bcrypt_like_hash}")

# Обновляем существующего админа или создаем нового
cursor.execute("""
    UPDATE users 
    SET hashed_password = ?, email = ?
    WHERE username = ?
""", (bcrypt_like_hash, email, username))

if cursor.rowcount == 0:
    # Если админ не найден, создаем нового
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, role, email_verified, totp_enabled)
        VALUES (?, ?, ?, 'admin', 1, 0)
    """, (username, email, bcrypt_like_hash))
    print("New admin user created!")
else:
    print("Existing admin user updated!")

conn.commit()
conn.close()

print("Admin user setup complete!")
print("You can now login with:")
print(f"Username: {username}")
print(f"Password: {password}")
