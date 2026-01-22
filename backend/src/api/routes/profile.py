"""
Additional auth routes for profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from src.models.database import get_db
from src.models.models import User
from src.api.routes.auth import get_current_user, verify_password, get_password_hash
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    try:
        # Update user fields
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        if profile_data.age is not None:
            current_user.age = profile_data.age
        if profile_data.guardian_contact is not None:
            current_user.guardian_contact = profile_data.guardian_contact
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"✅ Profile updated for user: {current_user.username}")
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "age": current_user.age,
                "guardian_contact": current_user.guardian_contact
            }
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.password_hash = get_password_hash(password_data.new_password)
        await db.commit()
        
        logger.info(f"✅ Password changed for user: {current_user.username}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
