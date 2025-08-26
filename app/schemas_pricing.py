from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Схемы для создания блоков ценообразования
class QuantityOptionCreate(BaseModel):
    name: str = Field(..., description="Название опции (например, 'Количество подушек')")
    unit_price: float = Field(..., description="Цена за единицу")
    min_quantity: int = Field(default=1, description="Минимальное количество")
    max_quantity: int = Field(default=100, description="Максимальное количество")
    unit_name: str = Field(..., description="Название единицы (штука, кв.м, окно)")

class TypeOptionCreate(BaseModel):
    name: str = Field(..., description="Название типа (например, 'Тип ткани')")
    options: List[dict] = Field(..., description="Список опций с ценами")

class ToggleOptionCreate(BaseModel):
    name: str = Field(..., description="Название опции (например, 'Ускоренная сушка')")
    short_description: str = Field(..., description="Краткое описание")
    full_description: Optional[str] = Field(None, description="Полное описание")
    percentage_increase: float = Field(..., description="Процент увеличения цены")

class PricingBlockCreate(BaseModel):
    name: str = Field(..., description="Название блока ценообразования")
    block_type: Literal["quantity", "type_choice", "toggle"] = Field(..., description="Тип блока")
    order_index: int = Field(default=0, description="Порядок отображения")
    is_required: bool = Field(default=True, description="Обязательный ли блок")
    
    # Опции в зависимости от типа блока
    quantity_options: Optional[QuantityOptionCreate] = None
    type_options: Optional[TypeOptionCreate] = None
    toggle_option: Optional[ToggleOptionCreate] = None

# Схемы для обновления
class PricingBlockUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    
    quantity_options: Optional[QuantityOptionCreate] = None
    type_options: Optional[TypeOptionCreate] = None
    toggle_option: Optional[ToggleOptionCreate] = None

# Схемы для ответов
class QuantityOptionResponse(BaseModel):
    id: int
    name: str
    unit_price: float
    min_quantity: int
    max_quantity: int
    unit_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class TypeOptionResponse(BaseModel):
    id: int
    name: str
    options: List[dict]
    created_at: datetime
    updated_at: Optional[datetime] = None

class ToggleOptionResponse(BaseModel):
    id: int
    name: str
    short_description: str
    full_description: Optional[str] = None
    percentage_increase: float
    created_at: datetime
    updated_at: Optional[datetime] = None

class PricingBlockResponse(BaseModel):
    id: int
    name: str
    block_type: str
    order_index: int
    is_required: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    quantity_options: Optional[QuantityOptionResponse] = None
    type_options: Optional[TypeOptionResponse] = None
    toggle_option: Optional[ToggleOptionResponse] = None

# Схемы для расчета цены
class PricingBlockSelection(BaseModel):
    block_id: int
    quantity: Optional[int] = None
    selected_type: Optional[str] = None
    toggle_enabled: Optional[bool] = None

class ServicePricingRequest(BaseModel):
    pricing_blocks: List[PricingBlockSelection]

class ServicePricingResponse(BaseModel):
    total_price: float
    base_price: float
    breakdown: List[dict]
    estimated_time_minutes: int

# Схемы для изменения порядка
class BlockOrder(BaseModel):
    block_id: int
    new_order: int
