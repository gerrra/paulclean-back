# Тесты ценообразования удалены, так как система ценообразования упрощена
# Теперь услуги содержат только базовую информацию: name, description, is_published

import pytest
from app.models import Service


class TestServiceModel:
    """Test simplified service model"""
    
    def test_service_creation(self):
        """Test basic service creation"""
        service = Service(
            name="Test Service",
            description="Test description",
            is_published=True
        )
        
        assert service.name == "Test Service"
        assert service.description == "Test description"
        assert service.is_published == True
    
    def test_service_creation_minimal(self):
        """Test service creation with minimal fields"""
        service = Service(
            name="Minimal Service"
        )
        
        assert service.name == "Minimal Service"
        assert service.description is None
        assert service.is_published is None  # По умолчанию None, не False
