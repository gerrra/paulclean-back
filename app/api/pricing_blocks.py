from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_admin
from app.models import User, Service, PricingBlock, QuantityOption, TypeOption, ToggleOption
from app.schemas_pricing import (
    PricingBlockCreate, PricingBlockUpdate, PricingBlockResponse,
    ServicePricingRequest, ServicePricingResponse, BlockOrder
)
import json
from typing import List

router = APIRouter()

@router.post("/services/{service_id}/pricing-blocks", response_model=PricingBlockResponse)
async def create_pricing_block(
    service_id: int,
    block_data: PricingBlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Создать новый блок ценообразования для услуги"""
    # Проверяем существование услуги
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Создаем блок ценообразования
    pricing_block = PricingBlock(
        service_id=service_id,
        name=block_data.name,
        block_type=block_data.block_type,
        order_index=block_data.order_index,
        is_required=block_data.is_required
    )
    db.add(pricing_block)
    db.flush()  # Получаем ID блока
    
    # Создаем опции в зависимости от типа блока
    if block_data.block_type == "quantity" and block_data.quantity_options:
        quantity_option = QuantityOption(
            pricing_block_id=pricing_block.id,
            name=block_data.quantity_options.name,
            unit_price=block_data.quantity_options.unit_price,
            min_quantity=block_data.quantity_options.min_quantity,
            max_quantity=block_data.quantity_options.max_quantity,
            unit_name=block_data.quantity_options.unit_name
        )
        db.add(quantity_option)
    
    elif block_data.block_type == "type_choice" and block_data.type_options:
        type_option = TypeOption(
            pricing_block_id=pricing_block.id,
            name=block_data.type_options.name,
            options=json.dumps(block_data.type_options.options)
        )
        db.add(type_option)
    
    elif block_data.block_type == "toggle" and block_data.toggle_option:
        toggle_option = ToggleOption(
            pricing_block_id=pricing_block.id,
            name=block_data.toggle_option.name,
            short_description=block_data.toggle_option.short_description,
            full_description=block_data.toggle_option.full_description,
            percentage_increase=block_data.toggle_option.percentage_increase
        )
        db.add(toggle_option)
    
    db.commit()
    db.refresh(pricing_block)
    
    return pricing_block

@router.get("/services/{service_id}/pricing-blocks", response_model=List[PricingBlockResponse])
async def get_service_pricing_blocks(
    service_id: int,
    db: Session = Depends(get_db)
):
    """Получить все блоки ценообразования для услуги"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    blocks = db.query(PricingBlock).filter(
        PricingBlock.service_id == service_id,
        PricingBlock.is_active == True
    ).order_by(PricingBlock.order_index).all()
    
    return blocks

@router.put("/pricing-blocks/{block_id}", response_model=PricingBlockResponse)
async def update_pricing_block(
    block_id: int,
    block_data: PricingBlockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Обновить блок ценообразования"""
    pricing_block = db.query(PricingBlock).filter(PricingBlock.id == block_id).first()
    if not pricing_block:
        raise HTTPException(status_code=404, detail="Блок ценообразования не найден")
    
    # Обновляем основные поля
    if block_data.name is not None:
        pricing_block.name = block_data.name
    if block_data.order_index is not None:
        pricing_block.order_index = block_data.order_index
    if block_data.is_required is not None:
        pricing_block.is_required = block_data.is_required
    if block_data.is_active is not None:
        pricing_block.is_active = block_data.is_active
    
    # Обновляем опции
    if block_data.quantity_options:
        # Удаляем старые опции
        db.query(QuantityOption).filter(QuantityOption.pricing_block_id == block_id).delete()
        
        # Создаем новые
        quantity_option = QuantityOption(
            pricing_block_id=block_id,
            name=block_data.quantity_options.name,
            unit_price=block_data.quantity_options.unit_price,
            min_quantity=block_data.quantity_options.min_quantity,
            max_quantity=block_data.quantity_options.max_quantity,
            unit_name=block_data.quantity_options.unit_name
        )
        db.add(quantity_option)
    
    if block_data.type_options:
        db.query(TypeOption).filter(TypeOption.pricing_block_id == block_id).delete()
        
        type_option = TypeOption(
            pricing_block_id=block_id,
            name=block_data.type_options.name,
            options=json.dumps(block_data.type_options.options)
        )
        db.add(type_option)
    
    if block_data.toggle_option:
        db.query(ToggleOption).filter(ToggleOption.pricing_block_id == block_id).delete()
        
        toggle_option = ToggleOption(
            pricing_block_id=block_id,
            name=block_data.toggle_option.name,
            short_description=block_data.toggle_option.short_description,
            full_description=block_data.toggle_option.full_description,
            percentage_increase=block_data.toggle_option.percentage_increase
        )
        db.add(toggle_option)
    
    db.commit()
    db.refresh(pricing_block)
    
    return pricing_block

@router.delete("/pricing-blocks/{block_id}")
async def delete_pricing_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Удалить блок ценообразования"""
    pricing_block = db.query(PricingBlock).filter(PricingBlock.id == block_id).first()
    if not pricing_block:
        raise HTTPException(status_code=404, detail="Блок ценообразования не найден")
    
    db.delete(pricing_block)
    db.commit()
    
    return {"message": "Блок ценообразования удален"}

@router.post("/services/{service_id}/pricing-blocks/reorder")
async def reorder_pricing_blocks(
    service_id: int,
    block_orders: List[BlockOrder],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Изменить порядок блоков ценообразования"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    for block_order in block_orders:
        block = db.query(PricingBlock).filter(
            PricingBlock.id == block_order.block_id,
            PricingBlock.service_id == service_id
        ).first()
        if block:
            block.order_index = block_order.new_order
    
    db.commit()
    
    return {"message": "Порядок блоков обновлен"}
