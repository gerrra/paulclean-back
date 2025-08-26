import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from app.config import settings

# Set up Jinja2 template environment
template_env = Environment(loader=FileSystemLoader('app/templates'))


class EmailService:
    """Email service for sending verification emails and notifications"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using configured SMTP settings"""
        if not settings.smtp_server:
            print(f"⚠️  SMTP not configured. Would send email to {to_email}: {subject}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.smtp_username or "noreply@cleaningservice.com"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connect to SMTP server
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                if settings.smtp_starttls:
                    server.starttls()
                
                # Only login if credentials are provided
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                
                # Send email
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_verification_email(email: str, verification_url: str, user_name: str) -> bool:
        """Send email verification email"""
        subject = "Verify Your Email - Cleaning Service"
        
        # Load and render template
        template = template_env.get_template('email_verification.html')
        html_content = template.render(
            user_name=user_name,
            verification_url=verification_url,
            support_email="support@cleaningservice.com"
        )
        
        # Plain text version
        text_content = f"""
        Hello {user_name},
        
        Please verify your email address by clicking the following link:
        {verification_url}
        
        This link will expire in {settings.email_verification_token_expire_hours} hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        Cleaning Service Team
        """
        
        return EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    def send_2fa_setup_email(email: str, qr_code_url: str, user_name: str) -> bool:
        """Send 2FA setup email"""
        subject = "Set Up Two-Factor Authentication - Cleaning Service"
        
        # Load and render template
        template = template_env.get_template('2fa_setup.html')
        html_content = template.render(
            user_name=user_name,
            qr_code_url=qr_code_url,
            support_email="support@cleaningservice.com"
        )
        
        # Plain text version
        text_content = f"""
        Hello {user_name},
        
        You've enabled two-factor authentication for your account.
        
        To complete the setup, scan the QR code in your authenticator app:
        {qr_code_url}
        
        If you have any questions, please contact support.
        
        Best regards,
        Cleaning Service Team
        """
        
        return EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    def send_password_reset_email(email: str, reset_url: str, user_name: str) -> bool:
        """Send password reset email"""
        subject = "Reset Your Password - Cleaning Service"
        
        # Load and render template
        template = template_env.get_template('password_reset.html')
        html_content = template.render(
            user_name=user_name,
            reset_url=reset_url,
            support_email="support@cleaningservice.com"
        )
        
        # Plain text version
        text_content = f"""
        Hello {user_name},
        
        You requested a password reset. Click the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Cleaning Service Team
        """
        
        return EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    def send_order_confirmation_email(email: str, order_details: dict, user_name: str) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmed - #{order_details.get('id', 'N/A')}"
        
        # Load and render template
        template = template_env.get_template('order_confirmation.html')
        html_content = template.render(
            user_name=user_name,
            order=order_details,
            support_email="support@cleaningservice.com"
        )
        
        # Plain text version
        text_content = f"""
        Hello {user_name},
        
        Your order has been confirmed!
        
        Order Details:
        - Order ID: {order_details.get('id', 'N/A')}
        - Date: {order_details.get('scheduled_date', 'N/A')}
        - Time: {order_details.get('scheduled_time', 'N/A')}
        - Total: ${order_details.get('total_price', 'N/A')}
        
        Thank you for choosing our service!
        
        Best regards,
        Cleaning Service Team
        """
        
        return EmailService.send_email(email, subject, html_content, text_content)
