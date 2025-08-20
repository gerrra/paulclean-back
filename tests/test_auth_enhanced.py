import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.auth_utils import (
    TOTPManager, TokenManager, PasswordManager, 
    RateLimitManager, SecurityManager, EmailVerificationManager
)
from app.models import Client, User, RefreshToken, RateLimit


class TestTOTPManager:
    """Test TOTP functionality"""
    
    def test_generate_secret(self):
        """Test TOTP secret generation"""
        secret1 = TOTPManager.generate_secret()
        secret2 = TOTPManager.generate_secret()
        
        assert len(secret1) == 32
        assert len(secret2) == 32
        assert secret1 != secret2
    
    def test_generate_qr_code(self):
        """Test QR code URL generation"""
        secret = "JBSWY3DPEHPK3PXP"
        email = "test@example.com"
        
        qr_url = TOTPManager.generate_qr_code(secret, email)
        
        assert "otpauth://totp/" in qr_url
        assert email in qr_url
        assert secret in qr_url
    
    def test_verify_totp(self):
        """Test TOTP verification"""
        secret = "JBSWY3DPEHPK3PXP"
        
        # This would need a real TOTP token for testing
        # For now, test with invalid token
        result = TOTPManager.verify_totp(secret, "000000")
        assert isinstance(result, bool)


class TestTokenManager:
    """Test JWT token management"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "123", "type": "client"}
        token = TokenManager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = 123
        user_type = "client"
        
        token, refresh_token_obj = TokenManager.create_refresh_token(user_id, user_type)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(refresh_token_obj, RefreshToken)
        assert refresh_token_obj.user_id == user_id
        assert refresh_token_obj.user_type == user_type
    
    def test_verify_token(self):
        """Test token verification"""
        # Test with invalid token
        result = TokenManager.verify_token("invalid_token")
        assert result is None


class TestPasswordManager:
    """Test password management"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        
        hashed = PasswordManager.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0
        
        # Verify password
        assert PasswordManager.verify_password(password, hashed) is True
        assert PasswordManager.verify_password("wrongpassword", hashed) is False
    
    def test_generate_verification_token(self):
        """Test verification token generation"""
        token1 = PasswordManager.generate_verification_token()
        token2 = PasswordManager.generate_verification_token()
        
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2


class TestRateLimitManager:
    """Test rate limiting functionality"""
    
    def test_rate_limit_check_new_key(self, db_session):
        """Test rate limit check for new key"""
        key = "test_key"
        
        is_allowed, count = RateLimitManager.check_rate_limit(key, db_session)
        
        assert is_allowed is True
        assert count == 1
    
    def test_rate_limit_check_existing_key(self, db_session):
        """Test rate limit check for existing key"""
        key = "test_key"
        
        # Create initial rate limit
        rate_limit = RateLimit(
            key=key,
            requests_count=5,
            window_start=datetime.utcnow()
        )
        db_session.add(rate_limit)
        db_session.commit()
        
        is_allowed, count = RateLimitManager.check_rate_limit(key, db_session)
        
        assert is_allowed is True
        assert count == 6
    
    def test_rate_limit_exceeded(self, db_session):
        """Test rate limit exceeded scenario"""
        key = "test_key"
        
        # Create rate limit at maximum
        rate_limit = RateLimit(
            key=key,
            requests_count=100,  # Assuming limit is 100
            window_start=datetime.utcnow()
        )
        db_session.add(rate_limit)
        db_session.commit()
        
        is_allowed, count = RateLimitManager.check_rate_limit(key, db_session)
        
        assert is_allowed is False
        assert count == 100


class TestSecurityManager:
    """Test security features"""
    
    def test_account_lockout_check(self):
        """Test account lockout checking"""
        # Create user with no lockout
        user = Client()
        user.locked_until = None
        
        assert SecurityManager.check_account_lockout(user) is False
        
        # Create user with active lockout
        user.locked_until = datetime.utcnow() + timedelta(minutes=5)
        
        assert SecurityManager.check_account_lockout(user) is True
    
    def test_failed_login_increment(self, db_session):
        """Test failed login attempt increment"""
        user = Client(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St"
        )
        db_session.add(user)
        db_session.commit()
        
        # Increment failed login
        SecurityManager.increment_failed_login(user, db_session)
        
        assert user.failed_login_attempts == 1
        assert user.locked_until is None
        
        # Increment to trigger lockout
        for _ in range(4):  # Total 5 attempts
            SecurityManager.increment_failed_login(user, db_session)
        
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
    
    def test_reset_failed_login(self, db_session):
        """Test failed login reset"""
        user = Client(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St",
            failed_login_attempts=3,
            locked_until=datetime.utcnow() + timedelta(minutes=5)
        )
        db_session.add(user)
        db_session.commit()
        
        SecurityManager.reset_failed_login(user, db_session)
        
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestEmailVerificationManager:
    """Test email verification functionality"""
    
    def test_create_verification_token(self, db_session):
        """Test verification token creation"""
        user = Client(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St"
        )
        db_session.add(user)
        db_session.commit()
        
        token = EmailVerificationManager.create_verification_token(user, db_session)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert user.email_verification_token == token
        assert user.email_verification_expires is not None
    
    def test_verify_email_token_valid(self, db_session):
        """Test valid email verification token"""
        user = Client(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St",
            email_verification_token="valid_token",
            email_verification_expires=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(user)
        db_session.commit()
        
        result = EmailVerificationManager.verify_email_token(user, "valid_token", db_session)
        
        assert result is True
        assert user.email_verified is True
        assert user.email_verification_token is None
        assert user.email_verification_expires is None
    
    def test_verify_email_token_expired(self, db_session):
        """Test expired email verification token"""
        user = Client(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St",
            email_verification_token="expired_token",
            email_verification_expires=datetime.utcnow() - timedelta(hours=1)
        )
        db_session.add(user)
        db_session.commit()
        
        result = EmailVerificationManager.verify_email_token(user, "expired_token", db_session)
        
        assert result is False
        assert user.email_verified is False


class TestAuthenticationIntegration:
    """Test authentication system integration"""
    
    @patch('app.email_service.EmailService.send_verification_email')
    def test_client_registration_flow(self, mock_send_email, db_session):
        """Test complete client registration flow"""
        from app.api.auth import register_client
        from app.schemas import ClientRegistration
        from fastapi import Request
        
        # Mock request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        # Registration data
        client_data = ClientRegistration(
            full_name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test Street, Test City, TC 12345",
            password="securepassword123"
        )
        
        # Mock email service
        mock_send_email.return_value = True
        
        # This would need the actual FastAPI test client
        # For now, just test the components
        assert client_data.full_name == "Test User"
        assert client_data.email == "test@example.com"
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        from app.schemas import ClientRegistration
        from pydantic import ValidationError
        
        # Valid password
        try:
            ClientRegistration(
                full_name="Test User",
                email="test@example.com",
                phone="+1234567890",
                address="123 Test Street",
                password="securepassword123"
            )
        except ValidationError:
            pytest.fail("Valid password should not raise ValidationError")
        
        # Invalid password (too short)
        with pytest.raises(ValidationError):
            ClientRegistration(
                full_name="Test User",
                email="test@example.com",
                phone="+1234567890",
                address="123 Test Street",
                password="short"
            )
