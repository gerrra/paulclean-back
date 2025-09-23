from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import (
    OrderCreate, OrderResponse, OrderCalculation, CalculationResponse,
    TimeslotsResponse
)
from app.models import Client, Order, OrderItem, Service, PricingBlock, QuantityOption, TypeOption, ToggleOption
from app.services import OrderService, PricingService
from app.config import settings
from app.schemas_pricing import ServicePricingRequest, ServicePricingResponse

router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order"""
    # Calculate total price and duration
    try:
        total_price, total_duration = OrderService.calculate_order_total(
            order_data.order_items, db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check timeslot availability
    if not OrderService.check_timeslot_availability(
        order_data.scheduled_date,
        order_data.scheduled_time,
        total_duration,
        db
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected timeslot is not available"
        )
    
    # Create order
    order = Order(
        client_id=current_user.id,
        scheduled_date=order_data.scheduled_date,
        scheduled_time=order_data.scheduled_time,
        total_duration_minutes=total_duration,
        total_price=total_price,
        notes=order_data.notes
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Create order items
    for item_data in order_data.order_items:
        service = db.query(Service).filter(Service.id == item_data.service_id).first()
        cost, duration = PricingService.calculate_service_cost(service, item_data.parameters)
        
        order_item = OrderItem(
            order_id=order.id,
            service_id=item_data.service_id,
            removable_cushion_count=item_data.parameters.removable_cushion_count,
            unremovable_cushion_count=item_data.parameters.unremovable_cushion_count,
            pillow_count=item_data.parameters.pillow_count,
            window_count=item_data.parameters.window_count,
            rug_width=item_data.parameters.rug_width,
            rug_length=item_data.parameters.rug_length,
            rug_count=item_data.parameters.rug_count,
            base_cleaning=item_data.parameters.base_cleaning,
            pet_hair=item_data.parameters.pet_hair,
            urine_stains=item_data.parameters.urine_stains,
            accelerated_drying=item_data.parameters.accelerated_drying,
            calculated_cost=cost,
            calculated_time_minutes=duration
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order details"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.client_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


def validate_date_format(date_str: str) -> str:
    """Validate date format and return the date string if valid"""
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD format."
        )



@router.post("/orders/calc", response_model=CalculationResponse)
async def calculate_order(
    calculation_data: OrderCalculation,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate order price and duration without saving"""
    try:
        total_price, total_duration = OrderService.calculate_order_total(
            calculation_data.order_items, db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create mock order items for response
    order_items = []
    for item_data in calculation_data.order_items:
        service = db.query(Service).filter(Service.id == item_data.service_id).first()
        cost, duration = PricingService.calculate_service_cost(service, item_data.parameters)
        
        # Create mock order item for response
        mock_order_item = type('MockOrderItem', (), {
            'id': 0,
            'service': service,
            'parameters': item_data.parameters,
            'calculated_cost': cost,
            'calculated_time_minutes': duration
        })()
        
        order_items.append(mock_order_item)
    
    return CalculationResponse(
        total_price=total_price,
        total_duration_minutes=total_duration,
        order_items=order_items
    )


# Authorized service pricing calculation
@router.post("/services/{service_id}/calculate-price", response_model=ServicePricingResponse)
async def calculate_service_price(
    service_id: int,
    pricing_data: ServicePricingRequest,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Рассчитать стоимость услуги на основе выбранных опций (требует авторизации)"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    if not service.is_published:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    
    # Загружаем блоки ценообразования
    pricing_blocks = db.query(PricingBlock).filter(
        PricingBlock.service_id == service_id,
        PricingBlock.is_active == True
    ).order_by(PricingBlock.order_index).all()
    
    service.pricing_blocks = pricing_blocks
    
    # Используем тот же калькулятор, что и в публичном API
    from app.api.public_pricing import PricingCalculator
    result = PricingCalculator.calculate_service_price(service, pricing_data)
    
    return ServicePricingResponse(
        total_price=result["total_price"],
        base_price=0,  # Пока не используем базовую цену
        breakdown=result["breakdown"],
        estimated_time_minutes=result["estimated_time_minutes"]
    )

