"""
RBAC Permission and Role Management Endpoints
Mental Health Chatbot - Permission, PermissionSet, and Role CRUD operations
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import logging

from src.models.database import get_db
from src.models.models import (
    User, Permission, PermissionSet, Role,
    PermissionSetPermission, RolePermissionSet
)
from src.api.dependencies import get_current_user, require_permission
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac", tags=["rbac"])

# ========== PYDANTIC MODELS ==========

class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    description: Optional[str]
    is_active: bool
    is_system: bool
    created_at: datetime

class PermissionSetResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    is_system: bool
    created_at: datetime
    permission_count: int

class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    is_system: bool
    is_default: bool
    created_at: datetime
    permission_count: int
    user_count: int

class PermissionSetCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    permission_ids: List[int]

class PermissionSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None

class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    permission_set_ids: Optional[List[int]] = []
    is_default: Optional[bool] = False

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    permission_set_ids: Optional[List[int]] = None


# ========== PERMISSION ENDPOINTS ==========

@router.get("/permissions", response_model=List[PermissionResponse], dependencies=[Depends(require_permission("permission.view"))])
async def list_permissions(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all permissions with optional filtering"""
    query = select(Permission).where(Permission.deleted_at == None)
    
    if category:
        query = query.where(Permission.category == category)
    if is_active is not None:
        query = query.where(Permission.is_active == is_active)
    
    query = query.order_by(Permission.category, Permission.name)
    result = await db.execute(query)
    permissions = result.scalars().all()
    
    return permissions


@router.get("/permissions/categories", dependencies=[Depends(require_permission("permission.view"))])
async def list_permission_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all unique permission categories"""
    result = await db.execute(
        select(Permission.category)
        .where(Permission.deleted_at == None)
        .distinct()
        .order_by(Permission.category)
    )
    categories = result.scalars().all()
    
    return {"categories": categories}


@router.get("/permissions/{permission_id}", response_model=PermissionResponse, dependencies=[Depends(require_permission("permission.view"))])
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific permission"""
    result = await db.execute(
        select(Permission).where(Permission.id == permission_id, Permission.deleted_at == None)
    )
    permission = result.scalar_one_or_none()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return permission


# ========== PERMISSION SET ENDPOINTS ==========

@router.get("/permission-sets", response_model=List[PermissionSetResponse], dependencies=[Depends(require_permission("permission.view"))])
async def list_permission_sets(
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all permission sets"""
    query = select(PermissionSet).where(PermissionSet.deleted_at == None)
    
    if is_active is not None:
        query = query.where(PermissionSet.is_active == is_active)
    
    query = query.options(selectinload(PermissionSet.permission_set_permissions))
    query = query.order_by(PermissionSet.name)
    result = await db.execute(query)
    permission_sets = result.scalars().all()
    
    response = []
    for ps in permission_sets:
        response.append({
            "id": ps.id,
            "code": ps.code,
            "name": ps.name,
            "description": ps.description,
            "is_active": ps.is_active,
            "is_system": ps.is_system,
            "created_at": ps.created_at,
            "permission_count": len(ps.permission_set_permissions)
        })
    
    return response


@router.post("/permission-sets", dependencies=[Depends(require_permission("permission.manage"))])
async def create_permission_set(
    permission_set: PermissionSetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new permission set"""
    # Check if code already exists
    result = await db.execute(
        select(PermissionSet).where(PermissionSet.code == permission_set.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Permission set code already exists")
    
    # Create permission set
    new_ps = PermissionSet(
        code=permission_set.code,
        name=permission_set.name,
        description=permission_set.description,
        is_system=False
    )
    db.add(new_ps)
    await db.flush()
    
    # Add permissions
    for perm_id in permission_set.permission_ids:
        psp = PermissionSetPermission(
            permission_set_id=new_ps.id,
            permission_id=perm_id
        )
        db.add(psp)
    
    await db.commit()
    await db.refresh(new_ps)
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "permission_set", "create",
        f"Created permission set {new_ps.code}", new_ps.id
    )
    
    return {"message": "Permission set created", "id": new_ps.id}


@router.put("/permission-sets/{ps_id}", dependencies=[Depends(require_permission("permission.manage"))])
async def update_permission_set(
    ps_id: int,
    permission_set: PermissionSetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a permission set"""
    result = await db.execute(
        select(PermissionSet).where(PermissionSet.id == ps_id, PermissionSet.deleted_at == None)
    )
    ps = result.scalar_one_or_none()
    
    if not ps:
        raise HTTPException(status_code=404, detail="Permission set not found")
    
    if ps.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system permission set")
    
    # Update basic fields
    update_data = permission_set.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for field, value in update_data.items():
        setattr(ps, field, value)
    
    # Update permissions if provided
    if permission_set.permission_ids is not None:
        # Remove old permissions
        await db.execute(
            select(PermissionSetPermission)
            .where(PermissionSetPermission.permission_set_id == ps_id)
        )
        await db.execute(
            PermissionSetPermission.__table__.delete()
            .where(PermissionSetPermission.permission_set_id == ps_id)
        )
        
        # Add new permissions
        for perm_id in permission_set.permission_ids:
            psp = PermissionSetPermission(
                permission_set_id=ps_id,
                permission_id=perm_id
            )
            db.add(psp)
    
    ps.updated_at = datetime.now()
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "permission_set", "update",
        f"Updated permission set {ps.code}", ps_id
    )
    
    return {"message": "Permission set updated"}


@router.delete("/permission-sets/{ps_id}", dependencies=[Depends(require_permission("permission.manage"))])
async def delete_permission_set(
    ps_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a permission set"""
    result = await db.execute(
        select(PermissionSet).where(PermissionSet.id == ps_id, PermissionSet.deleted_at == None)
    )
    ps = result.scalar_one_or_none()
    
    if not ps:
        raise HTTPException(status_code=404, detail="Permission set not found")
    
    if ps.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system permission set")
    
    ps.deleted_at = datetime.now()
    ps.is_active = False
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "permission_set", "delete",
        f"Deleted permission set {ps.code}", ps_id
    )
    
    return {"message": "Permission set deleted"}


@router.get("/permission-sets/{ps_id}/permissions", dependencies=[Depends(require_permission("permission.view"))])
async def get_permission_set_permissions(
    ps_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions in a permission set"""
    result = await db.execute(
        select(PermissionSet)
        .options(
            selectinload(PermissionSet.permission_set_permissions)
            .selectinload(PermissionSetPermission.permission)
        )
        .where(PermissionSet.id == ps_id, PermissionSet.deleted_at == None)
    )
    ps = result.scalar_one_or_none()
    
    if not ps:
        raise HTTPException(status_code=404, detail="Permission set not found")
    
    permissions = [
        {
            "id": psp.permission.id,
            "code": psp.permission.code,
            "name": psp.permission.name,
            "category": psp.permission.category
        }
        for psp in ps.permission_set_permissions
        if psp.permission.is_active
    ]
    
    return {"permissions": permissions, "count": len(permissions)}


# ========== ROLE ENDPOINTS ==========

@router.get("/roles", response_model=List[RoleResponse], dependencies=[Depends(require_permission("role.view"))])
async def list_roles(
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all roles with metadata"""
    query = select(Role).where(Role.deleted_at == None)
    
    if is_active is not None:
        query = query.where(Role.is_active == is_active)
    
    query = query.options(
        selectinload(Role.role_permission_sets),
        selectinload(Role.user_roles)
    )
    query = query.order_by(Role.name)
    result = await db.execute(query)
    roles = result.scalars().all()
    
    response = []
    for role in roles:
        permission_count = len(role.role_permission_sets)
        user_count = len([ur for ur in role.user_roles if not ur.user.deleted_at])
        
        response.append({
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "is_system": role.is_system,
            "is_default": role.is_default,
            "created_at": role.created_at,
            "permission_count": permission_count,
            "user_count": user_count
        })
    
    return response


@router.post("/roles", dependencies=[Depends(require_permission("role.create"))])
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role"""
    # Check if code exists
    result = await db.execute(
        select(Role).where(Role.code == role.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role code already exists")
    
    # Create role
    new_role = Role(
        code=role.code,
        name=role.name,
        description=role.description,
        is_default=role.is_default,
        is_system=False
    )
    db.add(new_role)
    await db.flush()
    
    # Add permission sets
    for ps_id in role.permission_set_ids:
        rps = RolePermissionSet(
            role_id=new_role.id,
            permission_set_id=ps_id
        )
        db.add(rps)
    
    await db.commit()
    await db.refresh(new_role)
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "role", "create",
        f"Created role {new_role.code}", new_role.id
    )
    
    return {"message": "Role created", "id": new_role.id}


@router.put("/roles/{role_id}", dependencies=[Depends(require_permission("role.edit"))])
async def update_role(
    role_id: int,
    role: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a role"""
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.deleted_at == None)
    )
    existing_role = result.scalar_one_or_none()
    
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if existing_role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")
    
    # Update basic fields
    update_data = role.model_dump(
        exclude_unset=True,
        exclude={"permission_set_ids"}
    )
    for field, value in update_data.items():
        setattr(existing_role, field, value)
    
    # Update permission sets if provided
    if role.permission_set_ids is not None:
        await db.execute(
            RolePermissionSet.__table__.delete()
            .where(RolePermissionSet.role_id == role_id)
        )
        for ps_id in role.permission_set_ids:
            rps = RolePermissionSet(
                role_id=role_id,
                permission_set_id=ps_id
            )
            db.add(rps)
    
    existing_role.updated_at = datetime.now()
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "role", "update",
        f"Updated role {existing_role.code}", role_id
    )
    
    return {"message": "Role updated"}


@router.delete("/roles/{role_id}", dependencies=[Depends(require_permission("role.delete"))])
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a role"""
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.deleted_at == None)
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    role.deleted_at = datetime.now()
    role.is_active = False
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "role", "delete",
        f"Deleted role {role.code}", role_id
    )
    
    return {"message": "Role deleted"}


@router.get("/roles/{role_id}/permissions", dependencies=[Depends(require_permission("role.view"))])
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all effective permissions for a role"""
    permissions = await PermissionService.get_role_permissions(db, role_id)
    return {"permissions": sorted(list(permissions)), "count": len(permissions)}
