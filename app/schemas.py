from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, date
from app.models import OrderStatus


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Authentication schemas
class ClientRegistration(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    address: str = Field(..., min_length=10, max_length=500)
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    totp_token: Optional[str] = Field(None, min_length=6, max_length=6)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: 'ClientResponse'


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional['UserResponse'] = None


class TOTPSetupRequest(BaseModel):
    totp_token: str = Field(..., min_length=6, max_length=6)


class TOTPSetupResponse(BaseModel):
    qr_code_url: str
    secret: str
    message: str


class TOTPVerifyRequest(BaseModel):
    totp_token: str = Field(..., min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    email_verified: bool


class EmailVerificationRequest(BaseModel):
    token: str


class ResendEmailVerificationRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class LogoutRequest(BaseModel):
    refresh_token: str


# Client schemas
class ClientResponse(BaseSchema):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    address: str
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ClientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    email_verified: Optional[bool] = None


class UserResponse(BaseSchema):
    id: int
    username: str
    email: EmailStr
    role: str
    email_verified: bool
    totp_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# Service schemas
class ServiceResponse(BaseSchema):
    id: int
    name: str
    description: str
    price_per_removable_cushion: float
    price_per_unremovable_cushion: float
    price_per_pillow: float
    price_per_window: float
    base_surcharge_pct: float
    pet_hair_surcharge_pct: float
    urine_stain_surcharge_pct: float
    accelerated_drying_surcharge: float
    before_image: Optional[str] = None
    after_image: Optional[str] = None
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    price_per_removable_cushion: Optional[float] = Field(0.0, ge=0)
    price_per_unremovable_cushion: Optional[float] = Field(0.0, ge=0)
    price_per_pillow: Optional[float] = Field(0.0, ge=0)
    price_per_window: Optional[float] = Field(0.0, ge=0)
    base_surcharge_pct: Optional[float] = Field(0.0, ge=0)
    pet_hair_surcharge_pct: Optional[float] = Field(0.0, ge=0)
    urine_stain_surcharge_pct: Optional[float] = Field(0.0, ge=0)
    accelerated_drying_surcharge: Optional[float] = Field(0.0, ge=0)
    before_image: Optional[str] = None
    after_image: Optional[str] = None
    is_published: Optional[bool] = False


# Cleaner schemas
class CleanerResponse(BaseSchema):
    id: int
    full_name: str
    phone: str
    email: EmailStr
    services: List[int]
    calendar_email: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CleanerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    email: EmailStr
    services: Optional[List[int]] = []
    calendar_email: Optional[EmailStr] = None


# Order schemas
class ServiceParameters(BaseModel):
    removable_cushion_count: Optional[int] = Field(0, ge=0)
    unremovable_cushion_count: Optional[int] = Field(0, ge=0)
    pillow_count: Optional[int] = Field(0, ge=0)
    window_count: Optional[int] = Field(0, ge=0)
    rug_width: Optional[float] = Field(0.0, ge=0)
    rug_length: Optional[float] = Field(0.0, ge=0)
    rug_count: Optional[int] = Field(1, ge=1)
    base_cleaning: Optional[bool] = False
    pet_hair: Optional[bool] = False
    urine_stains: Optional[bool] = False
    accelerated_drying: Optional[bool] = False


class OrderItemCreate(BaseModel):
    service_id: int
    parameters: ServiceParameters


class OrderCreate(BaseModel):
    scheduled_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    scheduled_time: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    order_items: List[OrderItemCreate] = Field(..., min_items=1)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('scheduled_date')
    def validate_future_date(cls, v):
        try:
            order_date = datetime.strptime(v, '%Y-%m-%d').date()
            if order_date <= date.today():
                raise ValueError('Order date must be in the future')
            return v
        except ValueError as e:
            if 'Order date must be in the future' in str(e):
                raise e
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

    @validator('scheduled_time')
    def validate_working_hours(cls, v):
        try:
            hour, minute = map(int, v.split(':'))
            if hour < 10 or hour >= 19:
                raise ValueError('Booking time must be between 10:00 and 19:00')
            if minute % 30 != 0:
                raise ValueError('Booking time must be in 30-minute increments')
            return v
        except ValueError as e:
            raise e


class OrderItemResponse(BaseSchema):
    id: int
    service: ServiceResponse
    parameters: ServiceParameters
    calculated_cost: float
    calculated_time_minutes: int


class OrderResponse(BaseSchema):
    id: int
    client: ClientResponse
    scheduled_date: str
    scheduled_time: str
    total_duration_minutes: int
    total_price: float
    status: str
    cleaner: Optional[CleanerResponse] = None
    notes: Optional[str] = None
    order_items: List[OrderItemResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = Field(None, max_length=1000)


class CleanerAssignment(BaseModel):
    cleaner_id: int


# Calculation schemas
class OrderCalculation(BaseModel):
    order_items: List[OrderItemCreate] = Field(..., min_items=1)


class CalculationResponse(BaseModel):
    total_price: float
    total_duration_minutes: int
    order_items: List[OrderItemResponse]


# Timeslot schemas
class TimeslotsResponse(BaseModel):
    date: str
    available_slots: List[str]
    working_hours: dict
    slot_duration_minutes: int


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


# Update forward references
LoginResponse.model_rebuild()
OrderResponse.model_rebuild()
