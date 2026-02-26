"""
Settings Management Endpoints with Version Control
Mental Health Chatbot - Configuration management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import logging

from src.models.database import get_db
from src.models.models import User
from src.api.dependencies import get_current_user, require_permission, require_any_permission
from src.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

# ========== PYDANTIC MODELS ==========

class SettingsUpdate(BaseModel):
    config: Dict[str, Any]
    change_description: Optional[str] = None

class SettingsResponse(BaseModel):
    segment: str
    config: Dict[str, Any]
    version: int
    updated_by: int
    updated_at: datetime
    change_description: Optional[str]

class VersionHistoryItem(BaseModel):
    version: int
    config: Dict[str, Any]
    updated_by: int
    updated_at: str
    change_description: Optional[str]
    is_current: Optional[bool] = False

class RollbackRequest(BaseModel):
    version: int


# ========== SETTINGS ENDPOINTS ==========

@router.get("/", dependencies=[Depends(require_any_permission("settings.view_basic", "settings.view_all"))])
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all settings segments"""
    settings = await SettingsService.get_settings(db)
    segments = await SettingsService.get_all_segments(db)
    
    return {
        "segments": segments,
        "settings": settings
    }


@router.get("/segments", dependencies=[Depends(require_any_permission("settings.view_basic", "settings.view_all"))])
async def list_segments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available settings segments"""
    segments = await SettingsService.get_all_segments(db)
    return {"segments": segments}


@router.get("/{segment}", dependencies=[Depends(require_any_permission("settings.view_basic", "settings.view_all"))])
async def get_segment_settings(
    segment: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get settings for a specific segment"""
    config = await SettingsService.get_settings(db, segment)
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Settings segment '{segment}' not found")
    
    return {
        "segment": segment,
        "config": config
    }


@router.put("/{segment}", dependencies=[Depends(require_any_permission("settings.edit_basic", "settings.edit_all"))])
async def update_segment_settings(
    segment: str,
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update settings for a specific segment"""
    # Validate configuration
    validation = await SettingsService.validate_config(segment, update.config)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid configuration", "errors": validation["errors"]}
        )
    
    # Update settings
    settings = await SettingsService.update_segment(
        db, segment, update.config, current_user.id, update.change_description
    )
    
    logger.info(f"✅ Settings segment '{segment}' updated to version {settings.version} by user {current_user.id}")
    
    return {
        "message": "Settings updated successfully",
        "segment": segment,
        "version": settings.version,
        "config": settings.config_value
    }


@router.get("/{segment}/history", dependencies=[Depends(require_any_permission("settings.view_all"))])
async def get_segment_history(
    segment: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version history for a settings segment"""
    history = await SettingsService.get_version_history(db, segment, limit)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history found for segment '{segment}'")
    
    return {
        "segment": segment,
        "history": history,
        "total_versions": len(history)
    }


@router.post("/{segment}/rollback", dependencies=[Depends(require_permission("settings.edit_all"))])
async def rollback_segment(
    segment: str,
    rollback: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rollback settings segment to a previous version"""
    try:
        settings = await SettingsService.rollback_to_version(
            db, segment, rollback.version, current_user.id
        )
        
        return {
            "message": f"Successfully rolled back '{segment}' to version {rollback.version}",
            "segment": segment,
            "new_version": settings.version,
            "config": settings.config_value
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise HTTPException(status_code=500, detail="Rollback failed")


@router.post("/{segment}/validate", dependencies=[Depends(require_any_permission("settings.edit_basic", "settings.edit_all"))])
async def validate_segment_config(
    segment: str,
    config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate configuration without saving"""
    validation = await SettingsService.validate_config(segment, config)
    
    return {
        "segment": segment,
        "valid": validation["valid"],
        "errors": validation.get("errors", [])
    }


# ========== COMMON SETTINGS SEGMENTS ==========

@router.get("/ai/config", dependencies=[Depends(require_any_permission("settings.view_basic", "ai.view"))])
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI configuration"""
    config = await SettingsService.get_settings(db, "ai_config")
    return {"segment": "ai_config", "config": config}


@router.get("/safety/config", dependencies=[Depends(require_any_permission("settings.view_all", "crisis.view_all"))])
async def get_safety_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get safety and crisis configuration"""
    config = await SettingsService.get_settings(db, "safety_config")
    return {"segment": "safety_config", "config": config}


@router.get("/features/flags", dependencies=[Depends(require_permission("settings.view_all"))])
async def get_feature_flags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feature flags"""
    config = await SettingsService.get_settings(db, "feature_flags")
    return {"segment": "feature_flags", "config": config}
