from app.auth import get_current_user
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth_utils import (
    TOTPManager, TokenManager, PasswordManager, 
    RateLimitManager, SecurityManager, EmailVerificationManager,
)
from app.email_service import EmailService
from app.schemas import (
    ClientRegistration, LoginRequest, LoginResponse, AdminLoginRequest, AdminLoginResponse,
    TOTPSetupRequest, TOTPSetupResponse, TOTPVerifyRequest, RefreshTokenRequest,
    RefreshTokenResponse, EmailVerificationRequest, PasswordResetRequest,
    PasswordResetConfirmRequest, LogoutRequest
)
from app.models import Client, User, RefreshToken
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register_client(
    request: Request,
    client_data: ClientRegistration,
    db: Session = Depends(get_db)
):
    """Client registration endpoint with email verification"""
    # Rate limiting
    client_ip = request.client.host
    rate_limit_key = f"register:{client_ip}"
    
    is_allowed, requests_count = RateLimitManager.check_rate_limit(rate_limit_key, db)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Try again later."
        )
    
    # Check if email already exists
    existing_client = db.query(Client).filter(Client.email == client_data.email).first()
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = PasswordManager.get_password_hash(client_data.password)
    
    # Create new client
    client = Client(
        full_name=client_data.full_name,
        email=client_data.email,
        phone=client_data.phone,
        address=client_data.address,
        hashed_password=hashed_password
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    
    # Send email verification
    if settings.email_verification_required:
        verification_token = EmailVerificationManager.create_verification_token(client, db)
        # Используем правильный URL для API endpoint с токеном
        verification_url = f"{request.base_url}verify-email/{verification_token}"
        
        # Отправляем email верификации
        email_sent = EmailService.send_verification_email(
            client.email, verification_url, client.full_name
        )
        
        if email_sent:
            print(f"✅ Verification email sent to {client.email}")
        else:
            print(f"❌ Failed to send verification email to {client.email}")
            # Не верифицируем автоматически - пользователь должен подтвердить email
            print(f"⚠️  Email verification required for {client.email} but SMTP not configured")
            # В продакшене здесь должен быть fallback механизм или уведомление администратора
    
    # Create access token and refresh token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = TokenManager.create_access_token(
        data={"sub": str(client.id), "type": "client"}, 
        expires_delta=access_token_expires
    )
    
    refresh_token, refresh_token_db = TokenManager.create_refresh_token(client.id, "client")
    db.add(refresh_token_db)
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=client
    )


@router.post("/login", response_model=LoginResponse)
async def login_client(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Client login endpoint with 2FA and rate limiting"""
    # Rate limiting
    client_ip = request.client.host
    rate_limit_key = f"login:{client_ip}"
    
    is_allowed, requests_count = RateLimitManager.check_rate_limit(rate_limit_key, db)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again later."
        )
    
    # Find client by email
    client = db.query(Client).filter(Client.email == login_data.email).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check account lockout
    if SecurityManager.check_account_lockout(client):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed attempts"
        )
    
    # Verify password
    if not PasswordManager.verify_password(login_data.password, client.hashed_password):
        SecurityManager.increment_failed_login(client, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if 2FA is required
    if client.totp_enabled:
        if not login_data.totp_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA token required"
            )
        
        if not TOTPManager.verify_totp(client.totp_secret, login_data.totp_token):
            SecurityManager.increment_failed_login(client, db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Check email verification
    print(f"🔍 Debug: email_verification_required = {settings.email_verification_required}")
    print(f"🔍 Debug: client.email_verified = {client.email_verified}")
    if settings.email_verification_required and not client.email_verified:
        print(f"❌ Debug: Blocking login - email not verified for {client.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link."
        )
    else:
        print(f"✅ Debug: Email verification check passed for {client.email}")
    
    # Reset failed login attempts
    SecurityManager.reset_failed_login(client, db)
    
    # Create access token and refresh token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = TokenManager.create_access_token(
        data={"sub": str(client.id), "type": "client"}, 
        expires_delta=access_token_expires
    )
    
    refresh_token, refresh_token_db = TokenManager.create_refresh_token(client.id, "client")
    db.add(refresh_token_db)
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=client
    )


@router.post("/admin/login", response_model=AdminLoginResponse)
async def login_admin(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint"""
    user = authenticate_admin(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = TokenManager.create_access_token(
        data={"sub": user.username, "type": "admin"}, 
        expires_delta=access_token_expires
    )
    
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        role=user.role
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Find refresh token
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user based on type
    if refresh_token.user_type == "client":
        user = db.query(Client).filter(Client.id == refresh_token.user_id).first()
        user_type = "client"
    else:
        user = db.query(User).filter(User.id == refresh_token.user_id).first()
        user_type = "user"
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token and refresh token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = TokenManager.create_access_token(
        data={"sub": str(user.id), "type": user_type}, 
        expires_delta=access_token_expires
    )
    
    # Revoke old refresh token and create new one
    TokenManager.revoke_refresh_token(refresh_data.refresh_token, db)
    new_refresh_token, new_refresh_token_db = TokenManager.create_refresh_token(user.id, user_type)
    db.add(new_refresh_token_db)
    db.commit()
    
    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    db: Session = Depends(get_db)
):
    """Logout and revoke refresh token"""
    TokenManager.revoke_refresh_token(logout_data.refresh_token, db)
    return {"message": "Successfully logged out"}


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify email address"""
    # Find user by verification token
    client = db.query(Client).filter(
        Client.email_verification_token == verification_data.token,
        Client.email_verification_expires > datetime.utcnow()
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Verify email
    if EmailVerificationManager.verify_email_token(client, verification_data.token, db):
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.get("/verify-email/{token}")
async def verify_email_get(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email address via GET request (for email links)"""
    # Find user by verification token
    client = db.query(Client).filter(
        Client.email_verification_token == token,
        Client.email_verification_expires > datetime.utcnow()
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Verify email
    if EmailVerificationManager.verify_email_token(client, token, db):
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.get("/verify-email")
async def verify_email_page():
    """Show verification page (for frontend integration)"""
    return {
        "message": "Email verification",
        "instructions": "Use the verification link from your email or provide token via POST request"
    }


@router.post("/setup-2fa", response_model=TOTPSetupResponse)
async def setup_2fa(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_user)
):
    """Setup 2FA for client account"""
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    # Generate TOTP secret
    totp_secret = TOTPManager.generate_secret()
    current_user.totp_secret = totp_secret
    db.commit()
    
    # Generate QR code URL
    qr_code_url = TOTPManager.generate_qr_code(totp_secret, current_user.email)
    
    # Send setup email
    EmailService.send_2fa_setup_email(
        current_user.email, qr_code_url, current_user.full_name
    )
    
    return TOTPSetupResponse(
        qr_code_url=qr_code_url,
        secret=totp_secret,
        message="2FA setup initiated. Check your email for QR code."
    )


@router.post("/enable-2fa")
async def enable_2fa(
    setup_data: TOTPSetupRequest,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_user)
):
    """Enable 2FA after verifying TOTP token"""
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    # Verify TOTP token
    if not TOTPManager.verify_totp(current_user.totp_secret, setup_data.totp_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP token"
        )
    
    # Enable 2FA
    current_user.totp_enabled = True
    db.commit()
    
    return {"message": "2FA enabled successfully"}


@router.post("/disable-2fa")
async def disable_2fa(
    verify_data: TOTPVerifyRequest,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_user)
):
    """Disable 2FA"""
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Verify TOTP token
    if not TOTPManager.verify_totp(current_user.totp_secret, verify_data.totp_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP token"
        )
    
    # Disable 2FA
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    
    return {"message": "2FA disabled successfully"}


@router.post("/password-reset")
async def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    # Rate limiting
    client_ip = request.client.host
    rate_limit_key = f"password_reset:{client_ip}"
    
    is_allowed, requests_count = RateLimitManager.check_rate_limit(rate_limit_key, db)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Try again later."
        )
    
    # Find user by email
    client = db.query(Client).filter(Client.email == reset_data.email).first()
    if client:
        # Generate reset token
        reset_token = PasswordManager.generate_verification_token()
        client.email_verification_token = reset_token
        client.email_verification_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # Send reset email
        reset_url = f"https://localhost/reset-password?token={reset_token}"
        EmailService.send_password_reset_email(
            client.email, reset_url, client.full_name
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    confirm_data: PasswordResetConfirmRequest,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    # Find user by reset token
    client = db.query(Client).filter(
        Client.email_verification_token == confirm_data.token,
        Client.email_verification_expires > datetime.utcnow()
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    client.hashed_password = PasswordManager.get_password_hash(confirm_data.new_password)
    client.email_verification_token = None
    client.email_verification_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/verify-token")
async def verify_token_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify if a token is valid and return user info"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Authorization header"
        )
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    token = auth_header.split(" ")[1]
    print(f"🔍 Debug: Verifying token: {token[:20]}...")
    
    payload = TokenManager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    print(f"✅ Debug: Token payload: {payload}")
    
    user_id = payload.get("sub")
    user_type = payload.get("type")
    
    if user_type == "client":
        user = db.query(Client).filter(Client.id == int(user_id)).first()
        if user:
            return {
                "valid": True,
                "user_type": "client",
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
    elif user_type == "admin":
        user = db.query(User).filter(User.username == user_id).first()
        if user:
            return {
                "valid": True,
                "user_type": "admin",
                "username": user.username
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found"
    )
