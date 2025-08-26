from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Service, PricingBlock, QuantityOption, TypeOption, ToggleOption
from app.schemas_pricing import ServicePricingRequest, ServicePricingResponse
import json
from typing import List

router = APIRouter()

class PricingCalculator:
    @staticmethod
    def calculate_service_price(service: Service, pricing_data: ServicePricingRequest) -> dict:
        total_price = 0.0
        breakdown = []
        estimated_time = 0
        
        for selection in pricing_data.pricing_blocks:
            block = next((b for b in service.pricing_blocks if b.id == selection.block_id), None)
            if not block or not block.is_active:
                continue
            
            if block.block_type == "quantity":
                price_info = PricingCalculator._calculate_quantity_price(block, selection)
                total_price += price_info["price"]
                breakdown.append(price_info)
                estimated_time += price_info.get("time_minutes", 0)
                
            elif block.block_type == "type_choice":
                price_info = PricingCalculator._calculate_type_price(block, selection)
                total_price += price_info["price"]
                breakdown.append(price_info)
                estimated_time += price_info.get("time_minutes", 0)
                
            elif block.block_type == "toggle":
                price_info = PricingCalculator._calculate_toggle_price(block, selection)
                total_price += price_info["price"]
                breakdown.append(price_info)
                estimated_time += price_info.get("time_minutes", 0)
        
        return {
            "total_price": total_price,
            "breakdown": breakdown,
            "estimated_time_minutes": estimated_time
        }
    
    @staticmethod
    def _calculate_quantity_price(block: PricingBlock, selection) -> dict:
        quantity_option = block.quantity_options[0] if block.quantity_options else None
        if not quantity_option:
            return {"price": 0, "description": f"{block.name}: опция не настроена"}
        
        quantity = selection.quantity or 0
        price = quantity * quantity_option.unit_price
        
        return {
            "block_name": block.name,
            "block_type": "quantity",
            "quantity": quantity,
            "unit_price": quantity_option.unit_price,
            "price": price,
            "description": f"{quantity} {quantity_option.unit_name} × ${quantity_option.unit_price}",
            "time_minutes": quantity * 15  # Примерное время: 15 минут на единицу
        }
    
    @staticmethod
    def _calculate_type_price(block: PricingBlock, selection) -> dict:
        type_option = block.type_options[0] if block.type_options else None
        if not type_option:
            return {"price": 0, "description": f"{block.name}: опция не настроена"}
        
        selected_type = selection.selected_type
        if not selected_type:
            return {"price": 0, "description": f"{block.name}: тип не выбран"}
        
        try:
            options = json.loads(type_option.options) if isinstance(type_option.options, str) else type_option.options
            selected_option = next((opt for opt in options if opt.get("name") == selected_type), None)
            
            if not selected_option:
                return {"price": 0, "description": f"{block.name}: выбранный тип не найден"}
            
            price = selected_option.get("price", 0)
            
            return {
                "block_name": block.name,
                "block_type": "type_choice",
                "selected_type": selected_type,
                "price": price,
                "description": f"{block.name}: {selected_type}",
                "time_minutes": 30  # Базовое время для выбора типа
            }
        except:
            return {"price": 0, "description": f"{block.name}: ошибка в настройках"}
    
    @staticmethod
    def _calculate_toggle_price(block: PricingBlock, selection) -> dict:
        toggle_option = block.toggle_option
        if not toggle_option:
            return {"price": 0, "description": f"{block.name}: опция не настроена"}
        
        if not selection.toggle_enabled:
            return {"price": 0, "description": f"{block.name}: отключено"}
        
        # Процентная надбавка применяется к базовой цене услуги
        # Здесь нужно будет передавать базовую цену или рассчитывать её отдельно
        percentage_increase = toggle_option.percentage_increase
        
        return {
            "block_name": block.name,
            "block_type": "toggle",
            "enabled": True,
            "percentage_increase": percentage_increase,
            "price": 0,  # Будет рассчитано на основе базовой цены
            "description": f"{block.name}: +{percentage_increase}%",
            "time_minutes": 0
        }

@router.post("/services/{service_id}/calculate-price", response_model=ServicePricingResponse)
async def calculate_service_price(
    service_id: int,
    pricing_data: ServicePricingRequest,
    db: Session = Depends(get_db)
):
    """Рассчитать стоимость услуги на основе выбранных опций"""
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
    
    # Рассчитываем цену
    result = PricingCalculator.calculate_service_price(service, pricing_data)
    
    return ServicePricingResponse(
        total_price=result["total_price"],
        base_price=0,  # Пока не используем базовую цену
        breakdown=result["breakdown"],
        estimated_time_minutes=result["estimated_time_minutes"]
    )

@router.get("/services/{service_id}/pricing-structure")
async def get_service_pricing_structure(
    service_id: int,
    db: Session = Depends(get_db)
):
    """Получить структуру ценообразования для услуги (для фронтенда)"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    if not service.is_published:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    
    pricing_blocks = db.query(PricingBlock).filter(
        PricingBlock.service_id == service_id,
        PricingBlock.is_active == True
    ).order_by(PricingBlock.order_index).all()
    
    structure = []
    for block in pricing_blocks:
        block_data = {
            "id": block.id,
            "name": block.name,
            "type": block.block_type,
            "required": block.is_required,
            "order": block.order_index
        }
        
        if block.block_type == "quantity" and block.quantity_options:
            quantity_option = block.quantity_options[0]
            block_data["quantity_options"] = {
                "name": quantity_option.name,
                "unit_price": quantity_option.unit_price,
                "min_quantity": quantity_option.min_quantity,
                "max_quantity": quantity_option.max_quantity,
                "unit_name": quantity_option.unit_name
            }
        
        elif block.block_type == "type_choice" and block.type_options:
            type_option = block.type_options[0]
            try:
                options = json.loads(type_option.options) if isinstance(type_option.options, str) else type_option.options
                block_data["type_options"] = {
                    "name": type_option.name,
                    "options": options
                }
            except:
                block_data["type_options"] = {"name": type_option.name, "options": []}
        
        elif block.block_type == "toggle" and block.toggle_option:
            toggle_option = block.toggle_option
            block_data["toggle_option"] = {
                "name": toggle_option.name,
                "short_description": toggle_option.short_description,
                "full_description": toggle_option.full_description,
                "percentage_increase": toggle_option.percentage_increase
            }
        
        structure.append(block_data)
    
    return {
        "service_id": service_id,
        "service_name": service.name,
        "pricing_structure": structure
    }
