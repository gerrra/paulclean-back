import pyotp
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User, Client, RefreshToken, RateLimit

# Configure CryptContext with truncate_error=False to allow auto-truncation
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False  # Auto-truncate passwords longer than 72 bytes
)


class TOTPManager:
    """TOTP (Time-based One-Time Password) management"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret: str, email: str) -> str:
        """Generate QR code URL for TOTP setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=settings.totp_issuer
        )
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=settings.totp_window)


class TokenManager:
    """JWT token management with refresh tokens"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        print(f"🔧 Debug: Creating token with data: {to_encode}")
        print(f"🔧 Debug: Using secret_key: {settings.secret_key[:20]}...")
        print(f"🔧 Debug: Using algorithm: {settings.algorithm}")
        
        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        print(f"✅ Debug: Token created: {token[:50]}...")
        return token
    
    @staticmethod
    def create_refresh_token(user_id: int, user_type: str) -> Tuple[str, RefreshToken]:
        """Create refresh token and store in database"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        refresh_token = RefreshToken(
            token=token,
            user_id=user_id,
            user_type=user_type,
            expires_at=expires_at
        )
        
        return token, refresh_token
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            print(f"🔍 Debug: Verifying token: {token[:20]}...")
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            print(f"✅ Debug: Token verified successfully: {payload}")
            return payload
        except JWTError as e:
            print(f"❌ Debug: JWT decode error: {e}")
            return None
        except Exception as e:
            print(f"❌ Debug: Unexpected error in verify_token: {e}")
            return None
    
    @staticmethod
    def revoke_refresh_token(token: str, db: Session) -> bool:
        """Revoke a refresh token"""
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.is_revoked == False
        ).first()
        
        if refresh_token:
            refresh_token.is_revoked = True
            db.commit()
            return True
        return False


class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        # Bcrypt has a maximum password length of 72 bytes
        # Truncate password if longer to avoid errors
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)


class RateLimitManager:
    """Rate limiting management"""
    
    @staticmethod
    def check_rate_limit(key: str, db: Session) -> Tuple[bool, int]:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=settings.rate_limit_window)
        
        # Get or create rate limit record
        rate_limit = db.query(RateLimit).filter(
            RateLimit.key == key,
            RateLimit.window_start >= window_start
        ).first()
        
        if not rate_limit:
            # Create new window
            rate_limit = RateLimit(
                key=key,
                requests_count=1,
                window_start=now
            )
            db.add(rate_limit)
            db.commit()
            return True, 1
        
        if rate_limit.requests_count >= settings.rate_limit_requests:
            return False, rate_limit.requests_count
        
        # Increment request count
        rate_limit.requests_count += 1
        db.commit()
        return True, rate_limit.requests_count
    
    @staticmethod
    def get_remaining_requests(key: str, db: Session) -> int:
        """Get remaining requests in current window"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=settings.rate_limit_window)
        
        rate_limit = db.query(RateLimit).filter(
            RateLimit.key == key,
            RateLimit.window_start >= window_start
        ).first()
        
        if not rate_limit:
            return settings.rate_limit_requests
        
        return max(0, settings.rate_limit_requests - rate_limit.requests_count)


class SecurityManager:
    """Security and account lockout management"""
    
    @staticmethod
    def check_account_lockout(user) -> bool:
        """Check if account is locked for both User and Client"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    @staticmethod
    def increment_failed_login(user, db: Session) -> None:
        """Increment failed login attempts for both User and Client"""
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        db.commit()
    
    @staticmethod
    def reset_failed_login(user, db: Session) -> None:
        """Reset failed login attempts for both User and Client"""
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
    
    @staticmethod
    def generate_secure_token() -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)


class EmailVerificationManager:
    """Email verification management"""
    
    @staticmethod
    def create_verification_token(user, db: Session) -> str:
        """Create email verification token for both User and Client"""
        token = PasswordManager.generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=settings.email_verification_token_expire_hours)
        
        user.email_verification_token = token
        user.email_verification_expires = expires_at
        db.commit()
        
        return token
    
    @staticmethod
    def verify_email_token(user, token: str, db: Session) -> bool:
        """Verify email verification token for both User and Client"""
        if (user.email_verification_token == token and 
            user.email_verification_expires and 
            user.email_verification_expires > datetime.utcnow()):
            
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def can_resend_verification(user) -> bool:
        """Check if verification email can be resent"""
        # If email is already verified, no need to resend
        if user.email_verified:
            return False
        
        # If no token exists, can resend
        if not user.email_verification_token:
            return True
        
        # If token is expired, can resend
        if not user.email_verification_expires or user.email_verification_expires <= datetime.utcnow():
            return True
        
        # If token is still valid, can resend (but will reuse existing token)
        return True
    
    @staticmethod
    def get_verification_status(user) -> dict:
        """Get verification status for user"""
        if user.email_verified:
            return {
                "verified": True,
                "has_valid_token": False,
                "message": "Email is already verified"
            }
        
        has_valid_token = (
            user.email_verification_token and 
            user.email_verification_expires and 
            user.email_verification_expires > datetime.utcnow()
        )
        
        return {
            "verified": False,
            "has_valid_token": has_valid_token,
            "message": "Email not verified"
        }
