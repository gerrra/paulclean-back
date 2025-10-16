from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import (
    OrderCreate, OrderResponse, OrderCalculation, CalculationResponse,
    TimeslotsResponse
)
from app.models import Client, Order, OrderItem, Service, PricingBlock, QuantityOption, TypeOption, ToggleOption
from app.services import OrderService
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
    
    # Create mock order items for response using PricingCalculator
    from app.api.public_pricing import PricingCalculator
    from app.schemas_pricing import ServicePricingRequest, PricingBlockSelection
    from app.models import PricingBlock
    
    order_items = []
    for item_data in calculation_data.order_items:
        service = db.query(Service).filter(Service.id == item_data.service_id).first()
        
        # Загружаем блоки ценообразования для услуги
        pricing_blocks = db.query(PricingBlock).filter(
            PricingBlock.service_id == item_data.service_id,
            PricingBlock.is_active == True
        ).order_by(PricingBlock.order_index).all()
        
        service.pricing_blocks = pricing_blocks
        
        # Конвертируем ServiceParameters в ServicePricingRequest
        pricing_selections = []
        for block in pricing_blocks:
            selection = PricingBlockSelection(block_id=block.id)
            
            if block.block_type == "quantity":
                if "cushion" in block.name.lower():
                    selection.quantity = item_data.parameters.removable_cushion_count + item_data.parameters.unremovable_cushion_count
                elif "pillow" in block.name.lower():
                    selection.quantity = item_data.parameters.pillow_count
                elif "window" in block.name.lower():
                    selection.quantity = item_data.parameters.window_count
                elif "rug" in block.name.lower():
                    selection.quantity = item_data.parameters.rug_count
            
            elif block.block_type == "toggle":
                if "base" in block.name.lower() or "cleaning" in block.name.lower():
                    selection.toggle_enabled = item_data.parameters.base_cleaning
                elif "pet" in block.name.lower() or "hair" in block.name.lower():
                    selection.toggle_enabled = item_data.parameters.pet_hair
                elif "urine" in block.name.lower() or "stain" in block.name.lower():
                    selection.toggle_enabled = item_data.parameters.urine_stains
                elif "drying" in block.name.lower() or "accelerated" in block.name.lower():
                    selection.toggle_enabled = item_data.parameters.accelerated_drying
            
            pricing_selections.append(selection)
        
        pricing_request = ServicePricingRequest(pricing_blocks=pricing_selections)
        
        # Рассчитываем цену через PricingCalculator
        result = PricingCalculator.calculate_service_price(service, pricing_request)
        cost = result["total_price"]
        duration = result["estimated_time_minutes"]
        
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


# Дублирующий endpoint удален - используется публичный endpoint из public_pricing.py

