from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Service, PricingOption, PerUnitOption, SelectorOption, PercentageOption
from app.schemas_pricing import (
    PublicServiceResponse, PublicPricingCalculationRequest, ServicePricingResponse
)

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/services", response_model=List[PublicServiceResponse])
def get_public_services(db: Session = Depends(get_db)):
    """Получить список опубликованных услуг с опциями ценообразования"""
    services = db.query(Service).filter(Service.is_published == True).all()
    return services


@router.get("/services/{service_id}", response_model=PublicServiceResponse)
def get_public_service(service_id: int, db: Session = Depends(get_db)):
    """Получить опубликованную услугу с опциями ценообразования"""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.is_published == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or not published"
        )
    
    # Получаем только видимые опции ценообразования
    pricing_options = db.query(PricingOption).filter(
        PricingOption.service_id == service_id,
        PricingOption.is_active == True,
        PricingOption.is_hidden == False  # Показываем только видимые опции
    ).order_by(PricingOption.order_index).all()
    
    # Временно заменяем опции услуги на видимые
    service.pricing_options = pricing_options
    return service


@router.post("/calculate-price", response_model=ServicePricingResponse)
def calculate_service_price(
    request: PublicPricingCalculationRequest,
    db: Session = Depends(get_db)
):
    """Рассчитать цену услуги на основе выбранных опций"""
    
    # Получаем услугу
    service = db.query(Service).filter(
        Service.id == request.service_id,
        Service.is_published == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or not published"
        )
    
    # Получаем все опции ценообразования для услуги (включая скрытые)
    pricing_options = db.query(PricingOption).filter(
        PricingOption.service_id == request.service_id,
        PricingOption.is_active == True
    ).order_by(PricingOption.order_index).all()
    
    if not pricing_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pricing options found for this service"
        )
    
    # Проверяем, что все обязательные видимые опции выбраны
    required_visible_options = [opt for opt in pricing_options if opt.is_required and not opt.is_hidden]
    selected_option_ids = [sel.option_id for sel in request.option_selections]
    
    for required_opt in required_visible_options:
        if required_opt.id not in selected_option_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required pricing option '{required_opt.name}' not selected"
            )
    
    # Рассчитываем цену
    total_price = 0.0
    base_price = 0.0
    breakdown = []
    estimated_time_minutes = 0
    
    # Сначала обрабатываем скрытые опции (они применяются автоматически)
    for option in pricing_options:
        if option.is_hidden and option.is_active:
            option_price = 0.0
            option_description = ""
            
            if option.option_type == "per_unit":
                per_unit_opt = db.query(PerUnitOption).filter(
                    PerUnitOption.pricing_option_id == option.id
                ).first()
                
                if per_unit_opt:
                    # Для скрытых опций используем минимальное количество
                    min_quantity = 1
                    option_price = per_unit_opt.price_per_unit * min_quantity
                    option_description = f"{option.name} (автоматически): {min_quantity} × ${per_unit_opt.price_per_unit:.2f}"
                    estimated_time_minutes += min_quantity * 15
            
            elif option.option_type == "selector":
                selector_opt = db.query(SelectorOption).filter(
                    SelectorOption.pricing_option_id == option.id
                ).first()
                
                if selector_opt and selector_opt.options:
                    # Для скрытых селекторов берем первую опцию
                    first_option = selector_opt.options[0]
                    min_quantity = 1
                    option_price = first_option["price"] * min_quantity
                    option_description = f"{option.name} (автоматически): {first_option['name']} × ${first_option['price']:.2f}"
                    estimated_time_minutes += min_quantity * 20
            
            elif option.option_type == "percentage":
                percentage_opt = db.query(PercentageOption).filter(
                    PercentageOption.pricing_option_id == option.id
                ).first()
                
                if percentage_opt:
                    # Процент будет применен позже к базовой цене
                    option_description = f"{option.name} (автоматически): +{percentage_opt.percentage_value}%"
                    estimated_time_minutes += 30
            
            total_price += option_price
            if option.option_type != "percentage":
                base_price += option_price
            
            if option_price > 0:
                breakdown.append({
                    "option_name": option.name,
                    "option_type": option.option_type,
                    "price": option_price,
                    "description": option_description,
                    "is_hidden": True
                })
    
    # Теперь обрабатываем видимые опции, выбранные пользователем
    for selection in request.option_selections:
        option = next((opt for opt in pricing_options if opt.id == selection.option_id), None)
        if not option or option.is_hidden:
            continue
        
        option_price = 0.0
        option_description = ""
        
        if option.option_type == "per_unit":
            # Цена за штуку
            per_unit_opt = db.query(PerUnitOption).filter(
                PerUnitOption.pricing_option_id == option.id
            ).first()
            
            if per_unit_opt and selection.quantity:
                option_price = per_unit_opt.price_per_unit * selection.quantity
                option_description = f"{option.name}: {selection.quantity} × ${per_unit_opt.price_per_unit:.2f}"
                estimated_time_minutes += selection.quantity * 15  # 15 минут на единицу
        
        elif option.option_type == "selector":
            # Селектор с ценой
            selector_opt = db.query(SelectorOption).filter(
                SelectorOption.pricing_option_id == option.id
            ).first()
            
            if selector_opt and selection.selected_option and selection.quantity:
                # Ищем выбранную опцию в списке
                selected_item = next(
                    (item for item in selector_opt.options if item["name"] == selection.selected_option),
                    None
                )
                
                if selected_item:
                    option_price = selected_item["price"] * selection.quantity
                    option_description = f"{option.name} - {selection.selected_option}: {selection.quantity} × ${selected_item['price']:.2f}"
                    estimated_time_minutes += selection.quantity * 20  # 20 минут на единицу
        
        elif option.option_type == "percentage":
            # Процентная надбавка
            percentage_opt = db.query(PercentageOption).filter(
                PercentageOption.pricing_option_id == option.id
            ).first()
            
            if percentage_opt and selection.enabled:
                # Процент применяется к текущей базовой цене
                option_price = base_price * (percentage_opt.percentage_value / 100)
                option_description = f"{option.name}: +{percentage_opt.percentage_value}%"
                estimated_time_minutes += 30  # 30 минут на процентную опцию
        
        total_price += option_price
        if option.option_type != "percentage":
            base_price += option_price
        
        if option_price > 0:
            breakdown.append({
                "option_name": option.name,
                "option_type": option.option_type,
                "price": option_price,
                "description": option_description,
                "is_hidden": False
            })
    
    # Теперь применяем процентные надбавки от скрытых опций к финальной базовой цене
    for option in pricing_options:
        if option.is_hidden and option.is_active and option.option_type == "percentage":
            percentage_opt = db.query(PercentageOption).filter(
                PercentageOption.pricing_option_id == option.id
            ).first()
            
            if percentage_opt:
                option_price = base_price * (percentage_opt.percentage_value / 100)
                total_price += option_price
                
                breakdown.append({
                    "option_name": option.name,
                    "option_type": option.option_type,
                    "price": option_price,
                    "description": f"{option.name} (автоматически): +{percentage_opt.percentage_value}%",
                    "is_hidden": True
                })
    
    return ServicePricingResponse(
        total_price=total_price,
        base_price=base_price,
        breakdown=breakdown,
        estimated_time_minutes=estimated_time_minutes
    )
