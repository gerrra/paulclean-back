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
        OrderStatus.PENDING_CONFIRMATION: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
        OrderStatus.COMPLETED: [],
        OrderStatus.CANCELLED: []
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
