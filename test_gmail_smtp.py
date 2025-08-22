#!/usr/bin/env python3
"""
Test script for Gmail SMTP connection
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('env.local')

def test_gmail_smtp():
    """Test Gmail SMTP connection"""
    
    # Get SMTP settings from environment
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_tls = os.getenv('SMTP_TLS', 'true').lower() == 'true'
    smtp_starttls = os.getenv('SMTP_STARTTLS', 'true').lower() == 'true'
    
    print(f"🔧 SMTP Settings:")
    print(f"  Server: {smtp_server}")
    print(f"  Port: {smtp_port}")
    print(f"  Username: {smtp_username}")
    print(f"  Password: {'*' * len(smtp_password) if smtp_password else 'None'}")
    print(f"  TLS: {smtp_tls}")
    print(f"  STARTTLS: {smtp_starttls}")
    
    if not smtp_username or not smtp_password:
        print("❌ SMTP_USERNAME или SMTP_PASSWORD не настроены в env.local")
        print("📝 Обновите env.local с вашими Gmail данными")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email - Cleaning Service"
        msg['From'] = smtp_username
        msg['To'] = "bogzaschita@gmail.com"
        
        # Add text content
        text_content = """
        Hello Bog Zaschita,
        
        This is a test email to verify SMTP configuration.
        
        Best regards,
        Cleaning Service Team
        """
        msg.attach(MIMEText(text_content, 'plain'))
        
        # Connect to SMTP server
        print(f"\n🔌 Подключение к {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        if smtp_starttls:
            print("🔒 Включение STARTTLS...")
            server.starttls()
        
        if smtp_username and smtp_password:
            print("🔐 Аутентификация...")
            server.login(smtp_username, smtp_password)
        
        # Send email
        print("📧 Отправка тестового email...")
        server.send_message(msg)
        
        print("✅ Email успешно отправлен!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e}")
        print("💡 Проверьте:")
        print("   - Включена ли 2FA в Gmail")
        print("   - Правильно ли создан App Password")
        print("   - Корректны ли данные в env.local")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ошибка: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тест Gmail SMTP подключения")
    print("=" * 50)
    
    success = test_gmail_smtp()
    
    if success:
        print("\n🎉 SMTP настроен правильно!")
        print("Теперь можно включить email verification в config.py")
    else:
        print("\n❌ SMTP не настроен")
        print("Следуйте инструкциям в SETUP_GMAIL_SMTP.md")
