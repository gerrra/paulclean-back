from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import ClientResponse, ClientUpdate
from app.models import Client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/profile", response_model=ClientResponse)
async def get_client_profile(
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current client profile"""
    logger.info(f"✅ Profile retrieved for client: {current_user.email}")
    return current_user


@router.put("/profile", response_model=ClientResponse)
async def update_client_profile(
    profile_data: ClientUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current client profile"""
    logger.info(f"🔄 Updating profile for client: {current_user.email}")
    logger.info(f"📝 Update data: {profile_data}")
    
    # Update only provided fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.address is not None:
        current_user.address = profile_data.address
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"✅ Profile updated successfully for client: {current_user.email}")
    return current_user


@router.get("/test-auth")
async def test_auth(current_user: Client = Depends(get_current_user)):
    """Test endpoint to verify authentication is working"""
    logger.info(f"🧪 Auth test successful for client: {current_user.email}")
    return {
        "message": "Authentication successful",
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }
