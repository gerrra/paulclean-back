import pytest
from app.services import PricingService
from app.models import Service
from app.schemas import ServiceParameters


class TestPricingService:
    """Test pricing calculation logic"""
    
    def test_couch_cleaning_basic(self):
        """Test basic couch cleaning pricing"""
        service = Service(
            price_per_removable_cushion=30.0,
            price_per_unremovable_cushion=18.0,
            price_per_pillow=5.0,
            base_surcharge_pct=38.0,
            pet_hair_surcharge_pct=15.0,
            urine_stain_surcharge_pct=5.0,
            accelerated_drying_surcharge=45.0,
            category="couch"
        )
        
        parameters = ServiceParameters(
            removable_cushion_count=2,
            unremovable_cushion_count=1,
            pillow_count=4
        )
        
        cost, duration = PricingService.calculate_service_cost(service, parameters)
        
        # Base calculation: 2*30 + 1*18 + 4*5 = 60 + 18 + 20 = 98
        expected_cost = 98.0
        assert cost == expected_cost
        assert duration == 120  # 2 hours for < $200
    
    def test_couch_cleaning_with_surcharges(self):
        """Test couch cleaning with all surcharges"""
        service = Service(
            price_per_removable_cushion=30.0,
            price_per_unremovable_cushion=18.0,
            price_per_pillow=5.0,
            base_surcharge_pct=38.0,
            pet_hair_surcharge_pct=15.0,
            urine_stain_surcharge_pct=5.0,
            accelerated_drying_surcharge=45.0,
            category="couch"
        )
        
        parameters = ServiceParameters(
            removable_cushion_count=3,
            unremovable_cushion_count=2,
            pillow_count=6,
            base_cleaning=True,
            pet_hair=True,
            urine_stains=True,
            accelerated_drying=True
        )
        
        cost, duration = PricingService.calculate_service_cost(service, parameters)
        
        # Base: 3*30 + 2*18 + 6*5 = 90 + 36 + 30 = 156
        # Base cleaning: 156 * 1.38 = 215.28
        # Pet hair: 215.28 * 1.15 = 247.57
        # Urine stains: 247.57 * 1.05 = 259.95
        # Accelerated drying: 259.95 + 45 = 304.95
        expected_cost = 304.95
        assert round(cost, 2) == expected_cost
        assert duration == 240  # 4 hours for $300-400
    
    def test_rug_cleaning(self):
        """Test rug cleaning pricing"""
        service = Service(category="rug")
        
        parameters = ServiceParameters(
            rug_width=8.0,
            rug_length=10.0,
            rug_count=2
        )
        
        cost, duration = PricingService.calculate_service_cost(service, parameters)
        
        # Area: 8 * 10 = 80 sq ft
        # Price: 80 * 2.5 * 2 = 400
        expected_cost = 400.0
        assert cost == expected_cost
        assert duration == 300  # 5 hours for $400-500
    
    def test_window_cleaning(self):
        """Test window cleaning pricing"""
        service = Service(
            price_per_window=25.0,
            category="window"
        )
        
        parameters = ServiceParameters(
            window_count=5
        )
        
        cost, duration = PricingService.calculate_service_cost(service, parameters)
        
        # Price: 5 * 25 = 125
        expected_cost = 125.0
        assert cost == expected_cost
        assert duration == 120  # 2 hours for < $200
    
    def test_cost_to_duration_mapping(self):
        """Test cost to duration mapping"""
        # Test all duration brackets
        assert PricingService._map_cost_to_duration(50) == 120    # < $120
        assert PricingService._map_cost_to_duration(150) == 120   # $120-200
        assert PricingService._map_cost_to_duration(250) == 180   # $200-300
        assert PricingService._map_cost_to_duration(350) == 240   # $300-400
        assert PricingService._map_cost_to_duration(450) == 300   # $400-500
        assert PricingService._map_cost_to_duration(600) == 360   # $500+
    
    def test_other_service_category(self):
        """Test other service category pricing"""
        service = Service(category="other")
        parameters = ServiceParameters()
        
        cost, duration = PricingService.calculate_service_cost(service, parameters)
        
        assert cost == 50.0  # Default price
        assert duration == 120  # 2 hours for < $200
