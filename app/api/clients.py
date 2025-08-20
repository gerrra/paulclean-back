from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import ClientResponse, ClientUpdate
from app.models import Client

router = APIRouter()


@router.get("/profile", response_model=ClientResponse)
async def get_client_profile(
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current client profile"""
    return current_user


@router.put("/profile", response_model=ClientResponse)
async def update_client_profile(
    profile_data: ClientUpdate,
    current_user: Client = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current client profile"""
    # Update only provided fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.address is not None:
        current_user.address = profile_data.address
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
