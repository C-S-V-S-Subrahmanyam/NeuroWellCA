"""
Permission Service - Core RBAC authorization logic
Mental health-specific permission management
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Set, Optional, List, Dict, Any
from datetime import datetime
import logging

from src.models.models import (
    User, Permission, PermissionSet, Role,
    UserRole, UserPermission, UserPermissionSet,
    RbacAuditLog
)

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing and checking user permissions"""
    
    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: int) -> Set[str]:
        """
        Calculate effective permissions for a user.
        Combines permissions from:
        1. Roles → Permission Sets → Permissions
        2. Direct Permission Sets → Permissions
        3. Direct Permissions
        
        Returns set of permission codes (e.g., {'chat.view', 'assessment.create'})
        """
        permissions: Set[str] = set()
        
        try:
            # Get user with all RBAC relationships
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.user_roles).selectinload(UserRole.role).selectinload(Role.permission_sets).selectinload(RolePermissionSet.permission_set).selectinload(PermissionSet.permissions).selectinload(PermissionSetPermission.permission),
                    selectinload(User.user_permission_sets).selectinload(UserPermissionSet.permission_set).selectinload(PermissionSet.permissions).selectinload(PermissionSetPermission.permission),
                    selectinload(User.user_permissions).selectinload(UserPermission.permission)
                )
                .where(User.id == user_id, User.is_active == True, User.deleted_at == None)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User {user_id} not found or inactive")
                return permissions
            
            # 1. Get permissions from roles
            for user_role in user.user_roles:
                role = user_role.role
                if not role.is_active or role.deleted_at:
                    continue
                    
                for role_perm_set in role.permission_sets:
                    perm_set = role_perm_set.permission_set
                    if not perm_set.is_active or perm_set.deleted_at:
                        continue
                        
                    for psp in perm_set.permissions:
                        perm = psp.permission
                        if perm.is_active and not perm.deleted_at:
                            permissions.add(perm.code)
            
            # 2. Get permissions from direct permission sets
            for user_perm_set in user.user_permission_sets:
                perm_set = user_perm_set.permission_set
                if not perm_set.is_active or perm_set.deleted_at:
                    continue
                    
                for psp in perm_set.permissions:
                    perm = psp.permission
                    if perm.is_active and not perm.deleted_at:
                        permissions.add(perm.code)
            
            # 3. Get direct permissions
            for user_perm in user.user_permissions:
                perm = user_perm.permission
                if perm.is_active and not perm.deleted_at:
                    permissions.add(perm.code)
            
            logger.info(f"User {user_id} has {len(permissions)} effective permissions")
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return permissions
    
    @staticmethod
    async def check_permission(
        db: AsyncSession, 
        user_id: int, 
        permission_code: str
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            db: Database session
            user_id: User ID to check
            permission_code: Permission code (e.g., 'chat.create')
        
        Returns:
            True if user has permission, False otherwise
        """
        permissions = await PermissionService.get_user_permissions(db, user_id)
        return permission_code in permissions
    
    @staticmethod
    async def check_any_permission(
        db: AsyncSession,
        user_id: int,
        permission_codes: List[str]
    ) -> bool:
        """
        Check if user has ANY of the specified permissions.
        
        Args:
            db: Database session
            user_id: User ID to check
            permission_codes: List of permission codes
        
        Returns:
            True if user has at least one permission
        """
        permissions = await PermissionService.get_user_permissions(db, user_id)
        return any(code in permissions for code in permission_codes)
    
    @staticmethod
    async def check_all_permissions(
        db: AsyncSession,
        user_id: int,
        permission_codes: List[str]
    ) -> bool:
        """
        Check if user has ALL of the specified permissions.
        
        Args:
            db: Database session
            user_id: User ID to check
            permission_codes: List of permission codes
        
        Returns:
            True if user has all permissions
        """
        permissions = await PermissionService.get_user_permissions(db, user_id)
        return all(code in permissions for code in permission_codes)
    
    @staticmethod
    async def get_role_permissions(db: AsyncSession, role_id: int) -> Set[str]:
        """Get all permissions for a specific role"""
        permissions: Set[str] = set()
        
        try:
            result = await db.execute(
                select(Role)
                .options(
                    selectinload(Role.permission_sets)
                    .selectinload(RolePermissionSet.permission_set)
                    .selectinload(PermissionSet.permissions)
                    .selectinload(PermissionSetPermission.permission)
                )
                .where(Role.id == role_id, Role.is_active == True, Role.deleted_at == None)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                return permissions
            
            for role_perm_set in role.permission_sets:
                perm_set = role_perm_set.permission_set
                if not perm_set.is_active or perm_set.deleted_at:
                    continue
                    
                for psp in perm_set.permissions:
                    perm = psp.permission
                    if perm.is_active and not perm.deleted_at:
                        permissions.add(perm.code)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting role permissions: {e}")
            return permissions
    
    @staticmethod
    async def get_user_roles(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """Get all roles assigned to a user"""
        try:
            result = await db.execute(
                select(UserRole)
                .options(selectinload(UserRole.role))
                .where(UserRole.user_id == user_id)
            )
            user_roles = result.scalars().all()
            
            return [
                {
                    "id": ur.role.id,
                    "code": ur.role.code,
                    "name": ur.role.name,
                    "description": ur.role.description,
                    "is_system": ur.role.is_system,
                    "assigned_at": ur.assigned_at
                }
                for ur in user_roles
                if ur.role.is_active and not ur.role.deleted_at
            ]
            
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return []
    
    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession,
        user_id: int,
        role_id: int,
        assigned_by: Optional[int] = None
    ) -> bool:
        """Assign a role to a user"""
        try:
            # Check if already assigned
            result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Role {role_id} already assigned to user {user_id}")
                return True
            
            # Create new assignment
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                assigned_at=datetime.now()
            )
            db.add(user_role)
            
            # Log audit trail
            await PermissionService.log_rbac_change(
                db=db,
                entity_type="user_role",
                entity_id=user_id,
                action="assign",
                new_value={"role_id": role_id},
                changed_by=assigned_by
            )
            
            await db.commit()
            logger.info(f"Assigned role {role_id} to user {user_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error assigning role: {e}")
            return False
    
    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user_id: int,
        role_id: int,
        changed_by: Optional[int] = None
    ) -> bool:
        """Remove a role from a user"""
        try:
            result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            )
            user_role = result.scalar_one_or_none()
            
            if not user_role:
                logger.warning(f"Role {role_id} not assigned to user {user_id}")
                return False
            
            await db.delete(user_role)
            
            # Log audit trail
            await PermissionService.log_rbac_change(
                db=db,
                entity_type="user_role",
                entity_id=user_id,
                action="revoke",
                old_value={"role_id": role_id},
                changed_by=changed_by
            )
            
            await db.commit()
            logger.info(f"Removed role {role_id} from user {user_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error removing role: {e}")
            return False
    
    @staticmethod
    async def log_rbac_change(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_by: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log RBAC changes for audit trail"""
        try:
            audit_log = RbacAuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                changed_at=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit_log)
            # Don't commit here - let the calling function handle commits
            
        except Exception as e:
            logger.error(f"Error logging RBAC change: {e}")


# Import needed for type hints
from src.models.models import RolePermissionSet, PermissionSetPermission
