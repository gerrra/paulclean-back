import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
# Import all models to ensure they are registered with Base.metadata
from app.models import *
from app.auth import get_password_hash

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure all tables are created
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Drop all tables first to avoid conflicts
    Base.metadata.drop_all(bind=engine)
    # Create all tables fresh
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin user"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password=pwd_context.hash("admin123"),
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def sample_client(db_session):
    """Create a sample client"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    client = Client(
        full_name="John Doe",
        email="john@test.com",
        phone="+1234567890",
        address="123 Test St, Test City, TC 12345",
        hashed_password=pwd_context.hash("password123")
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def sample_service(db_session):
    """Create a sample service"""
    service = Service(
        name="Couch Cleaning",
        description="Professional deep cleaning for all types of couches",
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
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def sample_cleaner(db_session):
    """Create a sample cleaner"""
    cleaner = Cleaner(
        full_name="Jane Smith",
        phone="+1234567891",
        email="jane@test.com",
        calendar_email="jane@test.com"
    )
    db_session.add(cleaner)
    db_session.commit()
    db_session.refresh(cleaner)
    return cleaner


@pytest.fixture
def admin_token(sample_admin):
    """Get admin authentication token"""
    response = client.post("/api/admin/login", json={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]


@pytest.fixture
def client_token(sample_client):
    """Get client authentication token"""
    response = client.post("/api/login", json={
        "email": "john@test.com",
        "password": "password123"
    })
    return response.json()["access_token"]
