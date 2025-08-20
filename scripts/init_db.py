#!/usr/bin/env python3
"""
Database initialization script for Cleaning Service API
Creates sample data for testing and development
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User, Service, Client, Cleaner
from app.auth import get_password_hash


def init_database():
    """Initialize database with sample data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@cleaningservice.com",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)
        
        # Create sample services
        couch_service = Service(
            name="Couch Cleaning",
            description="Professional deep cleaning for all types of couches and sofas",
            category="couch",
            price_per_removable_cushion=30.0,
            price_per_unremovable_cushion=18.0,
            price_per_pillow=5.0,
            base_surcharge_pct=38.0,
            pet_hair_surcharge_pct=15.0,
            urine_stain_surcharge_pct=5.0,
            accelerated_drying_surcharge=45.0,
            is_published=True
        )
        db.add(couch_service)
        
        rug_service = Service(
            name="Rug & Carpet Cleaning",
            description="Deep cleaning and stain removal for rugs and carpets",
            category="rug",
            is_published=True
        )
        db.add(rug_service)
        
        window_service = Service(
            name="Window Cleaning",
            description="Professional window cleaning for residential and commercial",
            category="window",
            price_per_window=25.0,
            is_published=True
        )
        db.add(window_service)
        
        # Create sample client
        client = Client(
            full_name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            address="123 Main Street, Anytown, ST 12345",
            hashed_password=get_password_hash("password123"),
            email_verified=True  # For demo purposes
        )
        db.add(client)
        
        # Create sample cleaner
        cleaner = Cleaner(
            full_name="Jane Smith",
            phone="+1234567891",
            email="jane.smith@cleaningservice.com",
            calendar_email="jane.smith@cleaningservice.com"
        )
        db.add(cleaner)
        
        # Commit all changes
        db.commit()
        
        print("✅ Database initialized successfully!")
        print("\nSample data created:")
        print(f"  - Admin user: admin / admin123")
        print(f"  - Client: {client.email}")
        print(f"  - Services: {couch_service.name}, {rug_service.name}, {window_service.name}")
        print(f"  - Cleaner: {cleaner.full_name}")
        print(f"\nDatabase file: cleaning_service.db")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
