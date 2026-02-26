"""
Settings Service with Version History and Rollback
Mental Health Chatbot - Configuration management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json
import logging

from src.models.models import Setting

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing system settings with version control"""
    
    @staticmethod
    async def get_Setting(db: AsyncSession, segment: Optional[str] = None) -> Dict[str, Any]:
        """Get settings by segment or all settings"""
        query = select(Setting).where(Setting.deleted_at == None)
        
        if segment:
            query = query.where(Setting.segment == segment)
        
        result = await db.execute(query)
        settings = result.scalars().all()
        
        if not settings:
            return {}
        
        # Return as dictionary
        if segment:
            return settings[0].config_value if settings else {}
        
        # Return all segments
        return {s.segment: s.config_value for s in settings}
    
    @staticmethod
    async def update_segment(
        db: AsyncSession,
        segment: str,
        config: Dict[str, Any],
        user_id: int,
        change_description: Optional[str] = None
    ) -> Setting:
        """Update a specific settings segment with version control"""
        # Get existing settings
        result = await db.execute(
            select(Setting).where(
                and_(
                    Setting.segment == segment,
                    Setting.deleted_at == None
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Save current version to history
            if existing.version_history is None:
                existing.version_history = []
            
            existing.version_history.append({
                "version": existing.version,
                "config": existing.config_value,
                "updated_by": existing.updated_by,
                "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                "change_description": existing.change_description
            })
            
            # Update with new config
            existing.config_value = config
            existing.version += 1
            existing.updated_by = user_id
            existing.updated_at = datetime.now()
            existing.change_description = change_description or f"Updated {segment} configuration"
            
            await db.commit()
            await db.refresh(existing)
            return existing
        
        else:
            # Create new settings segment
            new_settings = Setting(
                segment=segment,
                config_value=config,
                version=1,
                updated_by=user_id,
                change_description=change_description or f"Initial {segment} configuration"
            )
            db.add(new_settings)
            await db.commit()
            await db.refresh(new_settings)
            return new_settings
    
    @staticmethod
    async def get_version_history(
        db: AsyncSession,
        segment: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get version history for a settings segment"""
        result = await db.execute(
            select(Setting).where(
                and_(
                    Setting.segment == segment,
                    Setting.deleted_at == None
                )
            )
        )
        settings = result.scalar_one_or_none()
        
        if not settings or not Setting.version_history:
            return []
        
        # Return most recent versions
        history = Setting.version_history[-limit:]
        history.reverse()  # Most recent first
        
        # Add current version at the top
        current = {
            "version": Setting.version,
            "config": Setting.config_value,
            "updated_by": Setting.updated_by,
            "updated_at": Setting.updated_at.isoformat() if Setting.updated_at else None,
            "change_description": Setting.change_description,
            "is_current": True
        }
        
        return [current] + history
    
    @staticmethod
    async def rollback_to_version(
        db: AsyncSession,
        segment: str,
        version: int,
        user_id: int
    ) -> Setting:
        """Rollback settings to a specific version"""
        result = await db.execute(
            select(Setting).where(
                and_(
                    Setting.segment == segment,
                    Setting.deleted_at == None
                )
            )
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            raise ValueError(f"Settings segment '{segment}' not found")
        
        if Setting.version == version:
            # Already at this version
            return settings
        
        # Find the version in history
        target_config = None
        if version == 0:
            raise ValueError("Cannot rollback to version 0")
        
        for hist in Setting.version_history:
            if hist["version"] == version:
                target_config = hist["config"]
                break
        
        if target_config is None:
            raise ValueError(f"Version {version} not found in history")
        
        # Save current version to history
        Setting.version_history.append({
            "version": Setting.version,
            "config": Setting.config_value,
            "updated_by": Setting.updated_by,
            "updated_at": Setting.updated_at.isoformat() if Setting.updated_at else None,
            "change_description": Setting.change_description
        })
        
        # Rollback
        Setting.config_value = target_config
        Setting.version += 1  # Increment version even on rollback
        Setting.updated_by = user_id
        Setting.updated_at = datetime.now()
        Setting.change_description = f"Rolled back to version {version}"
        
        await db.commit()
        await db.refresh(settings)
        
        logger.info(f"✅ Rolled back {segment} to version {version} (now version {Setting.version})")
        
        return settings
    
    @staticmethod
    async def get_all_segments(db: AsyncSession) -> List[str]:
        """Get list of all settings segments"""
        result = await db.execute(
            select(Setting.segment).where(Setting.deleted_at == None).distinct()
        )
        segments = result.scalars().all()
        return list(segments)
    
    @staticmethod
    async def validate_config(segment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration for a specific segment"""
        errors = []
        
        # Segment-specific validation
        if segment == "ai_config":
            required_fields = ["model", "temperature", "max_tokens"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            if "temperature" in config:
                temp = config["temperature"]
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    errors.append("Temperature must be between 0 and 2")
            
            if "max_tokens" in config:
                tokens = config["max_tokens"]
                if not isinstance(tokens, int) or tokens < 1:
                    errors.append("max_tokens must be a positive integer")
        
        elif segment == "safety_config":
            if "crisis_keywords" in config and not isinstance(config["crisis_keywords"], list):
                errors.append("crisis_keywords must be a list")
        
        elif segment == "feature_flags":
            # All feature flags should be boolean
            for key, value in config.items():
                if not isinstance(value, bool):
                    errors.append(f"Feature flag '{key}' must be boolean")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
