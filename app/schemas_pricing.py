from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


# Базовые схемы для опций ценообразования
class PerUnitOptionCreate(BaseModel):
    price_per_unit: float = Field(..., gt=0, description="Цена за единицу в долларах")
    short_description: Optional[str] = Field(None, max_length=200, description="Краткое описание")
    full_description: Optional[str] = Field(None, max_length=1000, description="Полное описание")


class SelectorOptionItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название элемента списка")
    price: float = Field(..., gt=0, description="Цена за единицу")
    short_description: Optional[str] = Field(None, max_length=200, description="Краткое описание")
    full_description: Optional[str] = Field(None, max_length=1000, description="Полное описание")


class SelectorOptionCreate(BaseModel):
    short_description: Optional[str] = Field(None, max_length=200, description="Краткое описание")
    full_description: Optional[str] = Field(None, max_length=1000, description="Полное описание")
    options: List[SelectorOptionItem] = Field(..., min_items=1, description="Список опций с ценами")


class PercentageOptionCreate(BaseModel):
    short_description: Optional[str] = Field(None, max_length=200, description="Краткое описание")
    full_description: Optional[str] = Field(None, max_length=1000, description="Полное описание")
    percentage_value: float = Field(..., gt=0, le=100, description="Значение процента (0-100)")


# Схема для создания опции ценообразования
class PricingOptionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название опции")
    option_type: Literal["per_unit", "selector", "percentage"] = Field(..., description="Тип опции")
    order_index: int = Field(default=0, ge=0, description="Порядок отображения")
    is_required: bool = Field(default=True, description="Обязательная ли опция")
    is_hidden: bool = Field(default=False, description="Скрытая опция (применяется по умолчанию)")
    
    # Конкретные опции в зависимости от типа
    per_unit_option: Optional[PerUnitOptionCreate] = None
    selector_option: Optional[SelectorOptionCreate] = None
    percentage_option: Optional[PercentageOptionCreate] = None
    
    @validator('per_unit_option')
    def validate_per_unit_option(cls, v, values):
        if values.get('option_type') == 'per_unit' and not v:
            raise ValueError('per_unit_option required for per_unit type')
        return v
    
    @validator('selector_option')
    def validate_selector_option(cls, v, values):
        if values.get('option_type') == 'selector' and not v:
            raise ValueError('selector_option required for selector type')
        return v
    
    @validator('percentage_option')
    def validate_percentage_option(cls, v, values):
        if values.get('option_type') == 'percentage' and not v:
            raise ValueError('percentage_option required for percentage type')
        return v


# Схемы для обновления
class PricingOptionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    order_index: Optional[int] = Field(None, ge=0)
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    is_hidden: Optional[bool] = None
    
    # Обновление конкретных опций
    per_unit_option: Optional[PerUnitOptionCreate] = None
    selector_option: Optional[SelectorOptionCreate] = None
    percentage_option: Optional[PercentageOptionCreate] = None


# Схемы для ответов
class PerUnitOptionResponse(BaseModel):
    id: int
    price_per_unit: float
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SelectorOptionItemResponse(BaseModel):
    name: str
    price: float
    short_description: Optional[str] = None
    full_description: Optional[str] = None


class SelectorOptionResponse(BaseModel):
    id: int
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    options: List[SelectorOptionItemResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None


class PercentageOptionResponse(BaseModel):
    id: int
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    percentage_value: float
    created_at: datetime
    updated_at: Optional[datetime] = None


class PricingOptionResponse(BaseModel):
    id: int
    name: str
    option_type: str
    order_index: int
    is_required: bool
    is_active: bool
    is_hidden: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Конкретные опции
    per_unit_option: Optional[PerUnitOptionResponse] = None
    selector_option: Optional[SelectorOptionResponse] = None
    percentage_option: Optional[PercentageOptionResponse] = None


# Схема для полной услуги с опциями ценообразования
class ServiceWithPricingResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_published: bool
    pricing_options: List['PricingOptionResponse']
    created_at: datetime
    updated_at: Optional[datetime] = None


# Схемы для расчета цены
class PricingOptionSelection(BaseModel):
    option_id: int
    quantity: Optional[int] = Field(None, gt=0)  # Для per_unit и selector
    selected_option: Optional[str] = None  # Для selector - название выбранной опции
    enabled: Optional[bool] = None  # Для percentage


class ServicePricingRequest(BaseModel):
    service_id: int
    option_selections: List[PricingOptionSelection]


class ServicePricingResponse(BaseModel):
    total_price: float
    base_price: float
    breakdown: List[Dict[str, Any]]
    estimated_time_minutes: int


# Схемы для изменения порядка
class OptionOrderUpdate(BaseModel):
    option_id: int
    new_order: int


# Схемы для публичного API
class PublicServiceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    pricing_options: List['PricingOptionResponse']


class PublicPricingCalculationRequest(BaseModel):
    service_id: int
    option_selections: List[PricingOptionSelection]
