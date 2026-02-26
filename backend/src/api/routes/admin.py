"""
Admin Management Routes
User management, role assignments, and direct permission management
Database stats and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.models.database import get_db
from src.models.models import (
    User, Assessment, Conversation, CrisisLog, ChatSession,
    Role, Permission, PermissionSet, UserRole, UserPermission, UserPermissionSet
)
from src.api.dependencies import require_permission, get_current_user
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models
class TableInfo(BaseModel):
    name: str
    row_count: int


class DatabaseStats(BaseModel):
    total_users: int
    total_conversations: int
    total_assessments: int
    total_crisis_logs: int
    total_sessions: int


class UserDetail(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    age: Optional[int]
    has_completed_initial_assessment: bool
    created_at: datetime
    last_login: Optional[datetime]


class ConversationDetail(BaseModel):
    id: int
    user_id: int
    session_id: str
    message_text: str
    sender: str
    crisis_detected: bool
    created_at: datetime


class AssessmentDetail(BaseModel):
    id: int
    user_id: int
    phq9_score: int
    gad7_score: int
    stress_level: int
    risk_level: str
    created_at: datetime


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overall database statistics"""
    try:
        # Count users
        user_count = await db.execute(select(func.count(User.id)))
        total_users = user_count.scalar() or 0
        
        # Count conversations
        conv_count = await db.execute(select(func.count(Conversation.id)))
        total_conversations = conv_count.scalar() or 0
        
        # Count assessments
        assess_count = await db.execute(select(func.count(Assessment.id)))
        total_assessments = assess_count.scalar() or 0
        
        # Count crisis logs
        crisis_count = await db.execute(select(func.count(CrisisLog.id)))
        total_crisis_logs = crisis_count.scalar() or 0
        
        # Count sessions
        session_count = await db.execute(select(func.count(ChatSession.id)))
        total_sessions = session_count.scalar() or 0
        
        return DatabaseStats(
            total_users=total_users,
            total_conversations=total_conversations,
            total_assessments=total_assessments,
            total_crisis_logs=total_crisis_logs,
            total_sessions=total_sessions
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/users", response_model=List[UserDetail])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all users (paginated)"""
    try:
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        users = result.scalars().all()
        
        return [
            UserDetail(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                age=user.age,
                has_completed_initial_assessment=user.has_completed_initial_assessment,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.get("/conversations", response_model=List[ConversationDetail])
async def get_all_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get conversations with optional filters"""
    try:
        query = select(Conversation).order_by(Conversation.created_at.desc())
        
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        if session_id:
            query = query.where(Conversation.session_id == session_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return [
            ConversationDetail(
                id=conv.id,
                user_id=conv.user_id,
                session_id=conv.session_id,
                message_text=conv.message_text,
                sender=conv.sender,
                crisis_detected=conv.crisis_detected or False,
                created_at=conv.created_at
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@router.get("/assessments", response_model=List[AssessmentDetail])
async def get_all_assessments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get assessments with optional filters"""
    try:
        query = select(Assessment).order_by(Assessment.created_at.desc())
        
        if user_id:
            query = query.where(Assessment.user_id == user_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        assessments = result.scalars().all()
        
        return [
            AssessmentDetail(
                id=assess.id,
                user_id=assess.user_id,
                phq9_score=assess.phq9_score,
                gad7_score=assess.gad7_score,
                stress_level=assess.stress_level,
                risk_level=assess.risk_level.value,
                created_at=assess.created_at
            )
            for assess in assessments
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assessments")


@router.get("/query", response_model=List[Dict[str, Any]])
async def execute_custom_query(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    query: str = Query(..., description="SQL SELECT query to execute")
):
    """Execute custom SQL query (SELECT only for safety)"""
    try:
        # Validate query is SELECT only
        query_lower = query.lower().strip()
        if not query_lower.startswith("select"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )
        
        # Execute query
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        # Convert to dict
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/tables", response_model=List[TableInfo])
async def get_table_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get information about all tables"""
    try:
        tables = [
            ("users", User),
            ("conversations", Conversation),
            ("assessments", Assessment),
            ("crisis_logs", CrisisLog),
            ("chat_sessions", ChatSession)
        ]
        
        table_info = []
        
        for table_name, model in tables:
            count_result = await db.execute(select(func.count()).select_from(model))
            row_count = count_result.scalar() or 0
            
            table_info.append(TableInfo(
                name=table_name,
                row_count=row_count
            ))
        
        return table_info
        
    except Exception as e:
        logger.error(f"❌ Failed to get table info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve table information")


# ========== NEW RBAC USER MANAGEMENT ENDPOINTS ==========

class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    roles: List[str]


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None


class RoleAssignment(BaseModel):
    role_id: int


class RoleListResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_system: bool
    assigned_at: Optional[datetime] = None


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str


class EffectivePermissionsResponse(BaseModel):
    user_id: int
    username: str
    permissions: List[str]
    permission_count: int
    roles: List[str]
    direct_permissions: List[str]
    direct_permission_sets: List[str]


@router.get("/rbac/users", response_model=dict, dependencies=[Depends(require_permission("user.view"))])
async def list_rbac_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users with RBAC info"""
    query = select(User).where(User.deleted_at == None)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.options(selectinload(User.user_roles).selectinload(UserRole.role))
    query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    users_data = []
    for user in users:
        roles = [ur.role.name for ur in user.user_roles if ur.role.is_active and not ur.role.deleted_at]
        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "roles": roles
        })
    
    return {
        "users": users_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.put("/rbac/users/{user_id}", dependencies=[Depends(require_permission("user.edit"))])
async def update_rbac_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User updated successfully", "user_id": user_id}


@router.delete("/rbac/users/{user_id}", dependencies=[Depends(require_permission("user.delete"))])
async def delete_rbac_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.deleted_at = datetime.now()
    user.is_active = False
    await db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/rbac/users/{user_id}/roles", response_model=List[RoleListResponse], dependencies=[Depends(require_permission("user.view"))])
async def get_user_roles_rbac(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles assigned to a user"""
    roles = await PermissionService.get_user_roles(db, user_id)
    return roles


@router.post("/rbac/users/{user_id}/roles", dependencies=[Depends(require_permission("user.manage_roles"))])
async def assign_role_rbac(
    user_id: int,
    role_assignment: RoleAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Role).where(Role.id == role_assignment.role_id, Role.deleted_at == None)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    success = await PermissionService.assign_role_to_user(
        db, user_id, role_assignment.role_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {"message": f"Role '{role.name}' assigned successfully"}


@router.delete("/rbac/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_permission("user.manage_roles"))])
async def remove_role_rbac(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a user"""
    success = await PermissionService.remove_role_from_user(
        db, user_id, role_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove role")
    
    return {"message": "Role removed successfully"}


@router.get("/rbac/users/{user_id}/permissions/effective", response_model=EffectivePermissionsResponse, dependencies=[Depends(require_permission("user.view"))])
async def get_effective_permissions_rbac(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all effective permissions for a user"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = await PermissionService.get_user_permissions(db, user_id)
    roles = await PermissionService.get_user_roles(db, user_id)
    role_names = [r["name"] for r in roles]
    
    result = await db.execute(
        select(UserPermission)
        .options(selectinload(UserPermission.permission))
        .where(UserPermission.user_id == user_id)
    )
    direct_perms = result.scalars().all()
    direct_perm_codes = [up.permission.code for up in direct_perms if up.permission.is_active]
    
    result = await db.execute(
        select(UserPermissionSet)
        .options(selectinload(UserPermissionSet.permission_set))
        .where(UserPermissionSet.user_id == user_id)
    )
    direct_sets = result.scalars().all()
    direct_set_codes = [ups.permission_set.code for ups in direct_sets if ups.permission_set.is_active]
    
    return {
        "user_id": user_id,
        "username": user.username,
        "permissions": sorted(list(permissions)),
        "permission_count": len(permissions),
        "roles": role_names,
        "direct_permissions": direct_perm_codes,
        "direct_permission_sets": direct_set_codes
    }
