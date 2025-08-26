from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_admin
from app.schemas import (
    OrderResponse, OrderStatusUpdate, CleanerAssignment,
    ServiceResponse, ServiceCreate, CleanerResponse, CleanerCreate
)
from app.models import User, Order, Service, Cleaner, OrderStatus
from app.services import CleanerService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Service, PricingOption, PerUnitOption, SelectorOption, PercentageOption
from app.schemas import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas_pricing import (
    PricingOptionCreate, PricingOptionUpdate, PricingOptionResponse,
    ServiceWithPricingResponse, OptionOrderUpdate
)

router = APIRouter()


# Order management endpoints
@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[OrderStatus] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all orders with optional filtering"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    if date_from:
        query = query.filter(Order.scheduled_date >= date_from)
    if date_to:
        query = query.filter(Order.scheduled_date <= date_to)
    
    orders = query.order_by(Order.scheduled_date.desc()).all()
    return orders


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update order status"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate status transition
    valid_transitions = {
        OrderStatus.pending: [OrderStatus.confirmed, OrderStatus.cancelled],
        OrderStatus.confirmed: [OrderStatus.completed, OrderStatus.cancelled],
        OrderStatus.completed: [],
        OrderStatus.cancelled: []
    }
    
    current_status = order.status
    new_status = status_update.status
    
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current_status} to {new_status}"
        )
    
    order.status = new_status
    if status_update.notes:
        order.notes = status_update.notes
    
    db.commit()
    db.refresh(order)
    
    return order


@router.put("/orders/{order_id}/cleaner", response_model=OrderResponse)
async def assign_cleaner(
    order_id: int,
    cleaner_assignment: CleanerAssignment,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Assign cleaner to order"""
    # Verify cleaner exists
    cleaner = db.query(Cleaner).filter(Cleaner.id == cleaner_assignment.cleaner_id).first()
    if not cleaner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleaner not found"
        )
    
    # Assign cleaner
    if CleanerService.assign_cleaner_to_order(order_id, cleaner_assignment.cleaner_id, db):
        order = db.query(Order).filter(Order.id == order_id).first()
        return order
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cleaner not available for this timeslot"
        )


# Service management endpoints
@router.get("/services", response_model=List[ServiceResponse])
async def list_services(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all services"""
    services = db.query(Service).all()
    return services


@router.post("/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    service_data: ServiceCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new service"""
    service = Service(**service_data.dict())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


# Cleaner management endpoints
@router.get("/cleaners", response_model=List[CleanerResponse])
async def list_cleaners(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all cleaners"""
    cleaners = db.query(Cleaner).all()
    return cleaners


@router.post("/cleaners", response_model=CleanerResponse, status_code=201)
async def create_cleaner(
    cleaner_data: CleanerCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new cleaner"""
    cleaner = Cleaner(**cleaner_data.dict())
    db.add(cleaner)
    db.commit()
    db.refresh(cleaner)
    return cleaner


# Управление услугами
@router.post("/services", response_model=ServiceResponse)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новую услугу"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create services"
        )
    
    db_service = Service(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@router.get("/services", response_model=List[ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список всех услуг"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view services"
        )
    
    return db.query(Service).all()


@router.get("/services/{service_id}", response_model=ServiceWithPricingResponse)
def get_service_with_pricing(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить услугу с опциями ценообразования"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view services"
        )
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service


@router.put("/services/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить услугу"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update services"
        )
    
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    for field, value in service_update.dict(exclude_unset=True).items():
        setattr(db_service, field, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service


@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить услугу"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete services"
        )
    
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    db.delete(db_service)
    db.commit()
    return {"message": "Service deleted successfully"}


# Управление опциями ценообразования
@router.post("/services/{service_id}/pricing-options", response_model=PricingOptionResponse)
def create_pricing_option(
    service_id: int,
    pricing_option: PricingOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать опцию ценообразования для услуги"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create pricing options"
        )
    
    # Проверяем существование услуги
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Создаем основную опцию
    db_pricing_option = PricingOption(
        service_id=service_id,
        name=pricing_option.name,
        option_type=pricing_option.option_type,
        order_index=pricing_option.order_index,
        is_required=pricing_option.is_required,
        is_hidden=pricing_option.is_hidden
    )
    db.add(db_pricing_option)
    db.commit()
    db.refresh(db_pricing_option)
    
    # Создаем конкретную опцию в зависимости от типа
    if pricing_option.option_type == "per_unit" and pricing_option.per_unit_option:
        per_unit = PerUnitOption(
            pricing_option_id=db_pricing_option.id,
            **pricing_option.per_unit_option.dict()
        )
        db.add(per_unit)
    
    elif pricing_option.option_type == "selector" and pricing_option.selector_option:
        selector = SelectorOption(
            pricing_option_id=db_pricing_option.id,
            **pricing_option.selector_option.dict()
        )
        db.add(selector)
    
    elif pricing_option.option_type == "percentage" and pricing_option.percentage_option:
        percentage = PercentageOption(
            pricing_option_id=db_pricing_option.id,
            **pricing_option.percentage_option.dict()
        )
        db.add(percentage)
    
    db.commit()
    db.refresh(db_pricing_option)
    return db_pricing_option


@router.get("/services/{service_id}/pricing-options", response_model=List[PricingOptionResponse])
def get_pricing_options(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить опции ценообразования для услуги"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view pricing options"
        )
    
    # Проверяем существование услуги
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return db.query(PricingOption).filter(PricingOption.service_id == service_id).order_by(PricingOption.order_index).all()


@router.put("/pricing-options/{option_id}", response_model=PricingOptionResponse)
def update_pricing_option(
    option_id: int,
    pricing_option_update: PricingOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить опцию ценообразования"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update pricing options"
        )
    
    db_option = db.query(PricingOption).filter(PricingOption.id == option_id).first()
    if not db_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing option not found"
        )
    
    # Обновляем основную опцию
    for field, value in pricing_option_update.dict(exclude_unset=True).items():
        if field not in ['per_unit_option', 'selector_option', 'percentage_option']:
            setattr(db_option, field, value)
    
    # Обновляем конкретные опции
    if pricing_option_update.per_unit_option and db_option.option_type == "per_unit":
        per_unit = db.query(PerUnitOption).filter(PerUnitOption.pricing_option_id == option_id).first()
        if per_unit:
            for field, value in pricing_option_update.per_unit_option.dict(exclude_unset=True).items():
                setattr(per_unit, field, value)
    
    elif pricing_option_update.selector_option and db_option.option_type == "selector":
        selector = db.query(SelectorOption).filter(SelectorOption.pricing_option_id == option_id).first()
        if selector:
            for field, value in pricing_option_update.selector_option.dict(exclude_unset=True).items():
                setattr(selector, field, value)
    
    elif pricing_option_update.percentage_option and db_option.option_type == "percentage":
        percentage = db.query(PercentageOption).filter(PercentageOption.pricing_option_id == option_id).first()
        if percentage:
            for field, value in pricing_option_update.percentage_option.dict(exclude_unset=True).items():
                setattr(percentage, field, value)
    
    db.commit()
    db.refresh(db_option)
    return db_option


@router.delete("/pricing-options/{option_id}")
def delete_pricing_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить опцию ценообразования"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete pricing options"
        )
    
    db_option = db.query(PricingOption).filter(PricingOption.id == option_id).first()
    if not db_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing option not found"
        )
    
    db.delete(db_option)
    db.commit()
    return {"message": "Pricing option deleted successfully"}


@router.put("/pricing-options/order")
def update_pricing_options_order(
    order_updates: List[OptionOrderUpdate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить порядок опций ценообразования"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update pricing options order"
        )
    
    for update in order_updates:
        db_option = db.query(PricingOption).filter(PricingOption.id == update.option_id).first()
        if db_option:
            db_option.order_index = update.new_order
    
    db.commit()
    return {"message": "Pricing options order updated successfully"}


@router.put("/services/{service_id}/publish")
def publish_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Опубликовать услугу"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can publish services"
        )
    
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    db_service.is_published = True
    db.commit()
    return {"message": "Service published successfully"}


@router.put("/services/{service_id}/unpublish")
def unpublish_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Снять услугу с публикации"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can unpublish services"
        )
    
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    db_service.is_published = False
    db.commit()
    return {"message": "Service unpublished successfully"}
