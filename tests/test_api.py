import pytest
from datetime import date, timedelta
from tests.conftest import client, admin_token, client_token


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_client_registration(self):
        """Test client registration"""
        response = client.post("/api/register", json={
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "address": "123 Test Street, Test City, TC 12345"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["full_name"] == "Test User"
    
    def test_client_login(self):
        """Test client login"""
        # First register a client
        client.post("/api/register", json={
            "full_name": "Login Test User",
            "email": "logintest@example.com",
            "phone": "+1234567891",
            "address": "456 Test Street, Test City, TC 12345"
        })
        
        # Then try to login
        response = client.post("/api/login", json={
            "email": "logintest@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_admin_login(self):
        """Test admin login"""
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["role"] == "admin"


class TestClientEndpoints:
    """Test client profile endpoints"""
    
    def test_get_client_profile(self, client_token):
        """Test getting client profile"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = client.get("/api/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "john@test.com"
        assert data["full_name"] == "John Doe"
    
    def test_update_client_profile(self, client_token):
        """Test updating client profile"""
        headers = {"Authorization": f"Bearer {client_token}"}
        update_data = {
            "full_name": "John Updated Doe",
            "phone": "+1987654321"
        }
        
        response = client.put("/api/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "John Updated Doe"
        assert data["phone"] == "+1987654321"


class TestOrderEndpoints:
    """Test order management endpoints"""
    
    def test_get_available_timeslots(self):
        """Test getting available timeslots"""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.get(f"/api/orders/slots?date={tomorrow}")
        
        assert response.status_code == 200
        data = response.json()
        assert "available_slots" in data
        assert "working_hours" in data
        assert data["date"] == tomorrow
    
    def test_calculate_order(self):
        """Test order calculation without saving"""
        calculation_data = {
            "order_items": [
                {
                    "service_id": 1,
                    "parameters": {
                        "removable_cushion_count": 2,
                        "unremovable_cushion_count": 1,
                        "pillow_count": 4
                    }
                }
            ]
        }
        
        response = client.post("/api/orders/calc", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_price" in data
        assert "total_duration_minutes" in data
        assert "order_items" in data
    
    def test_create_order(self, client_token):
        """Test creating a new order"""
        headers = {"Authorization": f"Bearer {client_token}"}
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        order_data = {
            "scheduled_date": tomorrow,
            "scheduled_time": "14:00",
            "order_items": [
                {
                    "service_id": 1,
                    "parameters": {
                        "removable_cushion_count": 2,
                        "unremovable_cushion_count": 1,
                        "pillow_count": 4
                    }
                }
            ],
            "notes": "Test order"
        }
        
        response = client.post("/api/orders", json=order_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["scheduled_date"] == tomorrow
        assert data["scheduled_time"] == "14:00"
        assert data["status"] == "Pending Confirmation"
        assert len(data["order_items"]) == 1


class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_list_orders(self, admin_token):
        """Test listing all orders"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/orders", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_services(self, admin_token):
        """Test listing all services"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/services", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_service(self, admin_token):
        """Test creating a new service"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        service_data = {
            "name": "Test Service",
            "description": "A test service for testing purposes",
            "category": "other",
            "price_per_window": 20.0
        }
        
        response = client.post("/api/admin/services", json=service_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Service"
        assert data["category"] == "other"
    
    def test_list_cleaners(self, admin_token):
        """Test listing all cleaners"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/cleaners", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_cleaner(self, admin_token):
        """Test creating a new cleaner"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        cleaner_data = {
            "full_name": "Test Cleaner",
            "phone": "+1234567892",
            "email": "cleaner@test.com"
        }
        
        response = client.post("/api/admin/cleaners", json=cleaner_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Test Cleaner"
        assert data["email"] == "cleaner@test.com"


class TestValidation:
    """Test input validation"""
    
    def test_invalid_date_format(self):
        """Test invalid date format validation"""
        response = client.get("/api/orders/slots?date=invalid-date")
        assert response.status_code == 400
    
    def test_past_date_validation(self):
        """Test past date validation in order creation"""
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = client.post("/api/orders/calc", json={
            "order_items": [
                {
                    "service_id": 1,
                    "parameters": {}
                }
            ]
        })
        
        # This should fail due to past date
        assert response.status_code == 400
    
    def test_invalid_time_format(self):
        """Test invalid time format validation"""
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        order_data = {
            "scheduled_date": tomorrow,
            "scheduled_time": "25:00",  # Invalid time
            "order_items": [
                {
                    "service_id": 1,
                    "parameters": {}
                }
            ],
            "notes": "Test order"
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 422  # Validation error
