from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# Enum для статуса заказа
class OrderStatus(str, enum.Enum):
    pending = "pending"           # Ожидает подтверждения
    confirmed = "confirmed"       # Подтвержден
    in_progress = "in_progress"   # В работе
    completed = "completed"       # Завершен
    cancelled = "cancelled"       # Отменен


# Many-to-many relationship between cleaners and services
cleaner_service = Table(
    'cleaner_service',
    Base.metadata,
    Column('cleaner_id', Integer, ForeignKey('cleaners.id')),
    Column('service_id', Integer, ForeignKey('services.id'))
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="admin")
    totp_secret = Column(String, nullable=True)  # 2FA secret
    totp_enabled = Column(Boolean, default=False)  # 2FA status
    email_verified = Column(Boolean, default=False)  # Email verification status
    email_verification_token = Column(String, nullable=True)  # Email verification token
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)  # Rate limiting
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    hashed_password = Column(String, nullable=True)  # Optional password for clients
    totp_secret = Column(String, nullable=True)  # 2FA secret
    totp_enabled = Column(Boolean, default=False)  # 2FA status
    email_verified = Column(Boolean, default=False)  # Email verification status
    email_verification_token = Column(String, nullable=True)  # Email verification token
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)  # Rate limiting
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="client")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)  # Can be User or Client ID
    user_type = Column(String, nullable=False)  # 'user' or 'client'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), onupdate=func.now())


class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True, nullable=False)  # IP address or user identifier
    requests_count = Column(Integer, default=0)
    window_start = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Новая упрощенная модель Service
class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Название услуги
    description = Column(Text, nullable=True)  # Краткое описание (необязательное)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="service")
    cleaners = relationship("Cleaner", secondary=cleaner_service, back_populates="services")
    pricing_options = relationship("PricingOption", back_populates="service", order_by="PricingOption.order_index")


# Новая модель для опций ценообразования
class PricingOption(Base):
    __tablename__ = "pricing_options"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    name = Column(String, nullable=False)  # Название опции
    option_type = Column(String, nullable=False)  # "per_unit", "selector", "percentage"
    order_index = Column(Integer, default=0)  # Порядок отображения
    is_required = Column(Boolean, default=True)  # Обязательная ли опция
    is_active = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)  # Скрытая опция (применяется по умолчанию)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service = relationship("Service", back_populates="pricing_options")
    per_unit_option = relationship("PerUnitOption", back_populates="pricing_option", uselist=False, cascade="all, delete-orphan")
    selector_option = relationship("SelectorOption", back_populates="pricing_option", uselist=False, cascade="all, delete-orphan")
    percentage_option = relationship("PercentageOption", back_populates="pricing_option", uselist=False, cascade="all, delete-orphan")


# 1. Цена за штуку
class PerUnitOption(Base):
    __tablename__ = "per_unit_options"
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_option_id = Column(Integer, ForeignKey("pricing_options.id"), nullable=False)
    price_per_unit = Column(Float, nullable=False)  # Цена в долларах
    short_description = Column(String, nullable=True)  # Краткое описание
    full_description = Column(Text, nullable=True)  # Полное описание
    
    # Relationships
    pricing_option = relationship("PricingOption", back_populates="per_unit_option")


# 2. Селектор с ценой за штуку
class SelectorOption(Base):
    __tablename__ = "selector_options"
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_option_id = Column(Integer, ForeignKey("pricing_options.id"), nullable=False)
    short_description = Column(String, nullable=True)  # Краткое описание
    full_description = Column(Text, nullable=True)  # Полное описание
    options = Column(JSON, nullable=False)  # JSON с опциями: [{"name": "Опция", "price": 10.0, "short_desc": "...", "full_desc": "..."}]
    
    # Relationships
    pricing_option = relationship("PricingOption", back_populates="selector_option")


# 3. Процент за включение опции
class PercentageOption(Base):
    __tablename__ = "percentage_options"
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_option_id = Column(Integer, ForeignKey("pricing_options.id"), nullable=False)
    short_description = Column(String, nullable=True)  # Краткое описание
    full_description = Column(Text, nullable=True)  # Полное описание
    percentage_value = Column(Float, nullable=False)  # Значение процента (например, 15.0 = +15%)
    
    # Relationships
    pricing_option = relationship("PricingOption", back_populates="percentage_option")


class Cleaner(Base):
    __tablename__ = "cleaners"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    calendar_email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    services = relationship("Service", secondary=cleaner_service, back_populates="cleaners")
    orders = relationship("Order", back_populates="cleaner")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    scheduled_date = Column(String, nullable=False)  # YYYY-MM-DD format
    scheduled_time = Column(String, nullable=False)  # HH:MM format
    total_duration_minutes = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default=OrderStatus.pending)
    cleaner_id = Column(Integer, ForeignKey("cleaners.id"), nullable=True)
    notes = Column(Text, nullable=True)
    google_calendar_event_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="orders")
    cleaner = relationship("Cleaner", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    selected_options = Column(JSON, nullable=False)  # JSON с выбранными опциями и значениями
    calculated_cost = Column(Float, nullable=False)
    calculated_time_minutes = Column(Integer, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    service = relationship("Service", back_populates="order_items")
