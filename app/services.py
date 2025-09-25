from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import Service, OrderItem, Order
from app.schemas import ServiceParameters, OrderItemCreate
from app.config import settings


class PricingService:
    """Service for calculating prices and durations based on business rules"""
    
    @staticmethod
    def calculate_service_cost(service: Service, parameters: ServiceParameters) -> Tuple[float, int]:
        """
        Calculate cost and time for a service based on parameters and business rules
        Returns: (cost, duration_minutes)
        """
        # Упрощенная система ценообразования - фиксированная цена за услугу
        base_cost = 100.0  # Базовая цена за услугу
        
        # Простая логика на основе параметров
        if parameters.rug_width > 0 and parameters.rug_length > 0:
            # Ценообразование для ковров на основе площади
            area = parameters.rug_width * parameters.rug_length
            base_cost = area * 2.5 * parameters.rug_count  # $2.50 за кв.фут
        elif parameters.window_count > 0:
            # Ценообразование для окон
            base_cost = parameters.window_count * 25.0  # $25 за окно
        elif parameters.removable_cushion_count > 0 or parameters.unremovable_cushion_count > 0 or parameters.pillow_count > 0:
            # Ценообразование для диванов
            base_cost = (
                parameters.removable_cushion_count * 30.0 +
                parameters.unremovable_cushion_count * 18.0 +
                parameters.pillow_count * 5.0
            )
        else:
            # Базовая цена для других услуг
            base_cost = 50.0
        
        # Применяем надбавки
        if parameters.base_cleaning:
            base_cost *= 1.38  # 38% надбавка за базовую чистку
        if parameters.pet_hair:
            base_cost *= 1.15  # 15% надбавка за шерсть животных
        if parameters.urine_stains:
            base_cost *= 1.05  # 5% надбавка за пятна мочи
        if parameters.accelerated_drying:
            base_cost += 45.0  # $45 за ускоренную сушку
        
        # Рассчитываем продолжительность на основе общей стоимости
        duration = PricingService._map_cost_to_duration(base_cost)
        
        return round(base_cost, 2), duration
    
    @staticmethod
    def _map_cost_to_duration(cost: float) -> int:
        """Map total cost to duration in minutes based on business rules"""
        if cost < 120:
            return 120  # 2 hours
        elif cost < 200:
            return 120  # 2 hours
        elif cost < 300:
            return 180  # 3 hours
        elif cost < 400:
            return 240  # 4 hours
        elif cost < 500:
            return 300  # 5 hours
        else:
            return 360  # 6 hours


class OrderService:
    """Service for order management and validation"""
    
    @staticmethod
    def calculate_order_total(order_items: List[OrderItemCreate], db: Session) -> Tuple[float, int]:
        """Calculate total price and duration for an order"""
        total_price = 0.0
        total_duration = 0
        
        for item in order_items:
            service = db.query(Service).filter(Service.id == item.service_id).first()
            if not service:
                raise ValueError(f"Service with id {item.service_id} not found")
            
            cost, duration = PricingService.calculate_service_cost(service, item.parameters)
            total_price += cost
            total_duration += duration
        
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
