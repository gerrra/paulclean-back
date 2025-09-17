from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    PENDING_CONFIRMATION = "Pending Confirmation"
    CONFIRMED = "Confirmed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"



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


class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price_per_removable_cushion = Column(Float, default=0.0)
    price_per_unremovable_cushion = Column(Float, default=0.0)
    price_per_pillow = Column(Float, default=0.0)
    price_per_window = Column(Float, default=0.0)
    base_surcharge_pct = Column(Float, default=0.0)
    pet_hair_surcharge_pct = Column(Float, default=0.0)
    urine_stain_surcharge_pct = Column(Float, default=0.0)
    accelerated_drying_surcharge = Column(Float, default=0.0)
    before_image = Column(String, nullable=True)
    after_image = Column(String, nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="service")
    cleaners = relationship("Cleaner", secondary=cleaner_service, back_populates="services")
    pricing_blocks = relationship("PricingBlock", back_populates="service", order_by="PricingBlock.order_index")


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
    status = Column(String, default=OrderStatus.PENDING_CONFIRMATION)
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
    removable_cushion_count = Column(Integer, default=0)
    unremovable_cushion_count = Column(Integer, default=0)
    pillow_count = Column(Integer, default=0)
    window_count = Column(Integer, default=0)
    rug_width = Column(Float, default=0.0)
    rug_length = Column(Float, default=0.0)
    rug_count = Column(Integer, default=1)
    base_cleaning = Column(Boolean, default=False)
    pet_hair = Column(Boolean, default=False)
    urine_stains = Column(Boolean, default=False)
    accelerated_drying = Column(Boolean, default=False)
    calculated_cost = Column(Float, nullable=False)
    calculated_time_minutes = Column(Integer, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    service = relationship("Service", back_populates="order_items")


# Новые модели для гибкой системы ценообразования
class PricingBlock(Base):
    __tablename__ = "pricing_blocks"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    name = Column(String, nullable=False)  # Название блока
    block_type = Column(String, nullable=False)  # "quantity", "type_choice", "toggle"
    order_index = Column(Integer, default=0)  # Порядок отображения
    is_required = Column(Boolean, default=True)  # Обязательный ли блок
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service = relationship("Service", back_populates="pricing_blocks")
    quantity_options = relationship("QuantityOption", back_populates="pricing_block", cascade="all, delete-orphan")
    type_options = relationship("TypeOption", back_populates="pricing_block", cascade="all, delete-orphan")
    toggle_option = relationship("ToggleOption", back_populates="pricing_block", cascade="all, delete-orphan", uselist=False)

class QuantityOption(Base):
    __tablename__ = "type_options"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_block_id = Column(Integer, ForeignKey("pricing_blocks.id"), nullable=False)
    name = Column(String, nullable=False)  # "Количество подушек", "Количество окон"
    unit_price = Column(Float, nullable=False)  # Цена за единицу
    min_quantity = Column(Integer, default=1)
    max_quantity = Column(Integer, default=100)
    unit_name = Column(String, nullable=False)  # "штука", "кв.м", "окно"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    pricing_block = relationship("PricingBlock", back_populates="quantity_options")

class TypeOption(Base):
    __tablename__ = "type_options"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_block_id = Column(Integer, ForeignKey("pricing_blocks.id"), nullable=False)
    name = Column(String, nullable=False)  # "Тип ткани", "Размер ковра"
    options = Column(Text, nullable=False)  # JSON строка с опциями
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    pricing_block = relationship("PricingBlock", back_populates="type_options")

class ToggleOption(Base):
    __tablename__ = "toggle_options"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    pricing_block_id = Column(Integer, ForeignKey("pricing_blocks.id"), nullable=False)
    name = Column(String, nullable=False)  # "Ускоренная сушка"
    short_description = Column(String, nullable=False)  # "Быстрая сушка"
    full_description = Column(Text, nullable=True)  # "Использование специального оборудования"
    percentage_increase = Column(Float, nullable=False)  # 15.0 = +15%
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    pricing_block = relationship("PricingBlock", back_populates="toggle_option")
