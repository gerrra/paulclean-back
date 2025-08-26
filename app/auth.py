from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User, Client
from app.auth_utils import TokenManager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Временная проверка для тестирования
    if plain_password == hashed_password:
        return True
    return pwd_context.verify(plain_password, hashed_password)
    # Временная проверка для тестирования
    if plain_password == "admin123" and hashed_password == "admin123":
        return True
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Client:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    print(f"🔐 Debug: Received token: {token[:20]}...")  # Логируем первые 20 символов токена
    
    payload = TokenManager.verify_token(token)
    if payload is None:
        print("❌ Debug: Token verification failed")
        raise credentials_exception
    
    print(f"✅ Debug: Token payload: {payload}")
    
    user_id: str = payload.get("sub")
    if user_id is None:
        print("❌ Debug: No 'sub' field in token payload")
        raise credentials_exception
    
    try:
        user_id_int = int(user_id)
        print(f"🔍 Debug: Looking for client with ID: {user_id_int}")
    except ValueError:
        print(f"❌ Debug: Invalid user_id format: {user_id}")
        raise credentials_exception
    
    user = db.query(Client).filter(Client.id == user_id_int).first()
    if user is None:
        print(f"❌ Debug: Client with ID {user_id_int} not found in database")
        raise credentials_exception
    
    print(f"✅ Debug: Found client: {user.email}")
    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = TokenManager.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user



def authenticate_admin(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None
def authenticate_client(db: Session, email: str, password: str) -> Optional[Client]:
    # For now, we'll use a simple approach where clients don't have passwords
    # In a real implementation, you'd want to add password fields to clients
    # or use a different authentication method
    client = db.query(Client).filter(Client.email == email).first()
    if client:
        # For demo purposes, accept any client with matching email
        # In production, implement proper password verification
        return client
    return None


