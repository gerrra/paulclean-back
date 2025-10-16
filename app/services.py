from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import Service, OrderItem, Order
from app.schemas import ServiceParameters, OrderItemCreate
from app.config import settings


# PricingService удален - теперь используется PricingCalculator из app/api/public_pricing.py


class OrderService:
    """Service for order management and validation"""
    
    @staticmethod
    def calculate_order_total(order_items: List[OrderItemCreate], db: Session) -> Tuple[float, int]:
        """Calculate total price and duration for an order using PricingCalculator"""
        from app.api.public_pricing import PricingCalculator
        from app.schemas_pricing import ServicePricingRequest, PricingBlockSelection
        
        total_price = 0.0
        total_duration = 0
        
        for item in order_items:
            service = db.query(Service).filter(Service.id == item.service_id).first()
            if not service:
                raise ValueError(f"Service with id {item.service_id} not found")
            
            # Загружаем блоки ценообразования для услуги
            from app.models import PricingBlock
            pricing_blocks = db.query(PricingBlock).filter(
                PricingBlock.service_id == item.service_id,
                PricingBlock.is_active == True
            ).order_by(PricingBlock.order_index).all()
            
            service.pricing_blocks = pricing_blocks
            
            # Конвертируем ServiceParameters в ServicePricingRequest
            pricing_selections = []
            for block in pricing_blocks:
                selection = PricingBlockSelection(block_id=block.id)
                
                if block.block_type == "quantity":
                    # Используем параметры из ServiceParameters для quantity блоков
                    if "cushion" in block.name.lower():
                        selection.quantity = item.parameters.removable_cushion_count + item.parameters.unremovable_cushion_count
                    elif "pillow" in block.name.lower():
                        selection.quantity = item.parameters.pillow_count
                    elif "window" in block.name.lower():
                        selection.quantity = item.parameters.window_count
                    elif "rug" in block.name.lower():
                        selection.quantity = item.parameters.rug_count
                
                elif block.block_type == "toggle":
                    # Используем параметры из ServiceParameters для toggle блоков
                    if "base" in block.name.lower() or "cleaning" in block.name.lower():
                        selection.toggle_enabled = item.parameters.base_cleaning
                    elif "pet" in block.name.lower() or "hair" in block.name.lower():
                        selection.toggle_enabled = item.parameters.pet_hair
                    elif "urine" in block.name.lower() or "stain" in block.name.lower():
                        selection.toggle_enabled = item.parameters.urine_stains
                    elif "drying" in block.name.lower() or "accelerated" in block.name.lower():
                        selection.toggle_enabled = item.parameters.accelerated_drying
                
                pricing_selections.append(selection)
            
            pricing_request = ServicePricingRequest(pricing_blocks=pricing_selections)
            
            # Рассчитываем цену через PricingCalculator
            result = PricingCalculator.calculate_service_price(service, pricing_request)
            total_price += result["total_price"]
            total_duration += result["estimated_time_minutes"]
        
        # Round duration to nearest 30 minutes
        total_duration = round(total_duration / 30) * 30
        
        return round(total_price, 2), total_duration
    
    @staticmethod
    def check_timeslot_availability(
        date: str, 
        time: str, 
        duration_minutes: int, 
        db: Session,
        exclude_order_id: int = None
    ) -> bool:
        """Check if a timeslot is available for booking"""
        # Parse date and time
        from datetime import datetime, timedelta
        
        try:
            start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        except ValueError:
            return False
        
        # Check working hours
        working_start = datetime.strptime(f"{date} {settings.working_hours_start}", "%Y-%m-%d %H:%M")
        working_end = datetime.strptime(f"{date} {settings.working_hours_end}", "%Y-%m-%d %H:%M")
        
        if start_datetime < working_start or end_datetime > working_end:
            return False
        
        # Check for overlapping orders
        query = db.query(Order).filter(
            Order.scheduled_date == date,
            Order.status.in_(["Pending Confirmation", "Confirmed"])
        )
        
        if exclude_order_id:
            query = query.filter(Order.id != exclude_order_id)
        
        existing_orders = query.all()
        
        for order in existing_orders:
            order_start = datetime.strptime(f"{date} {order.scheduled_time}", "%Y-%m-%d %H:%M")
            order_end = order_start + timedelta(minutes=order.total_duration_minutes)
            
            # Check for overlap
            if (start_datetime < order_end and end_datetime > order_start):
                return False
        
        return True
    
    @staticmethod
    def get_available_timeslots(date: str, db: Session) -> List[str]:
        """Get available timeslots for a given date"""
        from datetime import datetime, timedelta
        
        # Generate all possible slots
        working_start = datetime.strptime(f"{date} {settings.working_hours_start}", "%Y-%m-%d %H:%M")
        working_end = datetime.strptime(f"{date} {settings.working_hours_end}", "%Y-%m-%d %H:%M")
        
        slots = []
        current_time = working_start
        
        while current_time < working_end:
            slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=settings.slot_duration_minutes)
        
        # Filter out unavailable slots
        available_slots = []
        for slot in slots:
            # Check if slot is available (assuming 2-hour default duration)
            if OrderService.check_timeslot_availability(date, slot, 120, db):
                available_slots.append(slot)
        
        return available_slots


class CleanerService:
    """Service for cleaner management and assignment"""
    
    @staticmethod
    def assign_cleaner_to_order(order_id: int, cleaner_id: int, db: Session) -> bool:
        """Assign a cleaner to an order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return False
        
        # Check if cleaner is available for the timeslot
        if not OrderService.check_timeslot_availability(
            order.scheduled_date, 
            order.scheduled_time, 
            order.total_duration_minutes, 
            db, 
            order_id
        ):
            return False
        
        order.cleaner_id = cleaner_id
        db.commit()
        return True
