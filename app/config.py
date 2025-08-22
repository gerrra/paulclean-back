from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./cleaning_service.db"

    # JWT
    secret_key: str = "W89Fy8E_KisTX7c64UsV7VNVLwpEexEyFPBA2AwQyiM3T2RZUH949iIOfW9OhdW9h9tT0ymW4bo3DcHWNn0kJw"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # 2FA
    totp_issuer: str = "Cleaning Service"
    totp_window: int = 1

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 900

    # Email
    smtp_server: Optional[str] = "localhost"  # Локальный SMTP сервер для тестирования
    smtp_port: int = 1025  # Порт локального SMTP сервера
    smtp_username: Optional[str] = None  # Не нужен для локального сервера
    smtp_password: Optional[str] = None  # Не нужен для локального сервера
    smtp_tls: bool = False  # Отключаем TLS для локального сервера
    smtp_starttls: bool = False  # Отключаем STARTTLS для локального сервера

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

    # Redis
    redis_url: str = "redis://redis:6379"

    # CORS  (в .env укажи JSON-массив в CORS_ORIGINS)
    cors_origins: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file="env.local",  # Используем локальный файл для тестирования
        extra="ignore",          # НЕ падать из-за лишних ключей
    )


settings = Settings()

# Debug: Print settings to verify they're loaded correctly
print(f"🔧 Debug: Settings loaded:")
print(f"  - Secret key: {settings.secret_key[:20]}...")
print(f"  - Algorithm: {settings.algorithm}")
print(f"  - Email verification required: {settings.email_verification_required}")
print(f"  - SMTP server: {settings.smtp_server}")
print(f"  - SMTP port: {settings.smtp_port}")
