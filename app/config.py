from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./cleaning_service.db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # Reduced for security
    refresh_token_expire_days: int = 7
    
    # 2FA
    totp_issuer: str = "Cleaning Service"
    totp_window: int = 1  # Time window for TOTP validation
    
    # Rate Limiting
    rate_limit_requests: int = 100  # Requests per window
    rate_limit_window: int = 900  # 15 minutes in seconds
    
    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    smtp_starttls: bool = True
    
    # Email verification
    email_verification_required: bool = True
    email_verification_token_expire_hours: int = 24
    
    # Google Calendar
    google_credentials_file: Optional[str] = None
    google_token_file: Optional[str] = None
    
    # Working hours
    working_hours_start: str = "10:00"
    working_hours_end: str = "19:00"
    slot_duration_minutes: int = 30
    
    # Redis (for rate limiting and sessions)
    redis_url: str = "redis://localhost:6379"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "https://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        env_file = ".env"


settings = Settings()
