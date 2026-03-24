"""
Authentication Dependencies
Permission-based authorization decorators for FastAPI
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from typing import Optional, List, Callable
from datetime import datetime
import logging

from src.models.database import get_db
from src.models.models import User, RevokedToken
from src.utils.config import settings
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    Validates token, checks if revoked, and token version.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = int(payload.get("sub"))
        jti: Optional[str] = payload.get("jti")  # JWT ID for revocation
        token_version: Optional[int] = payload.get("token_version")
        
        if user_id is None:
            raise credentials_exception
    
    except JWTError:
        raise credentials_exception
    
    # Check if token is revoked
    if jti:
        result = await db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or deleted"
        )
    
    # Check token version (invalidates all old tokens)
    user_token_version = user.token_version or 1
    if token_version is not None and user_token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is no longer valid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_permission(permission_code: str):
    """
    Dependency decorator to require a specific permission.
    
    Usage:
        @router.get("/crisis", dependencies=[Depends(require_permission("crisis.view"))])
        async def view_crisis():
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_perm = await PermissionService.check_permission(
            db, current_user.id, permission_code
        )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code} required"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(*permission_codes: str):
    """
    Dependency decorator to require ANY of the specified permissions.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_any_permission("admin.view", "system.manage"))])
        async def admin_panel():
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_perm = await PermissionService.check_any_permission(
            db, current_user.id, list(permission_codes)
        )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: One of {permission_codes} required"
            )
        
        return current_user
    
    return permission_checker


def require_all_permissions(*permission_codes: str):
    """
    Dependency decorator to require ALL of the specified permissions.
    
    Usage:
        @router.post("/critical", dependencies=[Depends(require_all_permissions("crisis.manage", "user.edit"))])
        async def critical_action():
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_perm = await PermissionService.check_all_permissions(
            db, current_user.id, list(permission_codes)
        )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: All of {permission_codes} required"
            )
        
        return current_user
    
    return permission_checker


async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """
    Get all permissions for the current user.
    Can be injected as a dependency to get user's permissions.
    
    Usage:
        async def my_endpoint(permissions: List[str] = Depends(get_user_permissions)):
            if "admin.view" in permissions:
                # Do admin stuff
    """
    perms = await PermissionService.get_user_permissions(db, current_user.id)
    return list(perms)


async def get_request_context(request: Request):
    """Extract request context for audit logging"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "path": str(request.url.path)
    }


# Legacy role-based auth (deprecated, use permissions instead)
def require_role(role_name: str):
    """
    DEPRECATED: Use require_permission() instead.
    
    Legacy role-based authentication for backward compatibility.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        # Get user roles
        user_roles = await PermissionService.get_user_roles(db, current_user.id)
        role_codes = [r["code"] for r in user_roles]
        
        if role_name not in role_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        
        return current_user
    
    return role_checker
