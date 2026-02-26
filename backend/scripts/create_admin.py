"""
Create initial Super Administrator user for NeurowellCA
Run this script once during initial setup
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from getpass import getpass

from src.models.database import AsyncSessionLocal
from src.models.models import User, Role, UserRole
from src.services.permission_service import PermissionService


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_super_admin():
    """Create initial super administrator"""
    print("=" * 60)
    print("NeurowellCA - Initial Super Administrator Setup")
    print("=" * 60)
    print()
    
    # Get admin details
    username = input("Admin Username: ").strip()
    email = input("Admin Email: ").strip()
    full_name = input("Full Name: ").strip()
    
    while True:
        password = getpass("Password: ")
        password_confirm = getpass("Confirm Password: ")
        
        if password == password_confirm:
            break
        print("Passwords don't match. Try again.")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where(
                    (User.username == username) | (User.email == email)
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\nError: User with username '{username}' or email '{email}' already exists!")
                return False
            
            # Create user
            password_hash = pwd_context.hash(password)
            admin_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                is_active=True,
                email_verified=True,
                has_completed_initial_assessment=True
            )
            
            db.add(admin_user)
            await db.flush()  # Get user ID
            
            print(f"\n✓ Created user account (ID: {admin_user.id})")
            
            # Get super_admin role
            result = await db.execute(
                select(Role).where(Role.code == "super_admin")
            )
            super_admin_role = result.scalar_one_or_none()
            
            if not super_admin_role:
                print("\nError: super_admin role not found in database!")
                print("Please run Alembic migrations first: python -m alembic upgrade head")
                await db.rollback()
                return False
            
            # Assign super_admin role
            await PermissionService.assign_role_to_user(
                db=db,
                user_id=admin_user.id,
                role_id=super_admin_role.id,
                assigned_by=admin_user.id  # Self-assigned
            )
            
            print(f"✓ Assigned 'Super Administrator' role")
            
            # Get effective permissions
            permissions = await PermissionService.get_user_permissions(db, admin_user.id)
            
            print(f"\n{'='*60}")
            print("SUCCESS! Super Administrator created successfully")
            print(f"{'='*60}")
            print(f"\nUsername: {username}")
            print(f"Email: {email}")
            print(f"Permissions: {len(permissions)} (full system access)")
            print(f"\nYou can now log in with these credentials.")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"\nError creating admin: {e}")
            import traceback
            traceback.print_exc()
            return False


async def verify_rbac_setup():
    """Verify RBAC system is properly set up"""
    print("\nVerifying RBAC setup...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check permissions
            result = await db.execute(select(Permission))
            permissions = result.scalars().all()
            print(f"✓ Permissions: {len(permissions)}")
            
            # Check permission sets
            result = await db.execute(select(PermissionSet))
            perm_sets = result.scalars().all()
            print(f"✓ Permission Sets: {len(perm_sets)}")
            
            # Check roles
            result = await db.execute(select(Role))
            roles = result.scalars().all()
            print(f"✓ Roles: {len(roles)}")
            
            # List available roles
            print("\nAvailable roles:")
            for role in roles:
                print(f"  - {role.name} ({role.code}): {role.description}")
            
            return True
            
        except Exception as e:
            print(f"\nError verifying RBAC: {e}")
            print("\nPlease run migrations first:")
            print("  cd backend")
            print("  python -m alembic upgrade head")
            return False


async def main():
    """Main setup function"""
    # Verify RBAC is set up
    if not await verify_rbac_setup():
        return 1
    
    print()
    
    # Create admin
    if await create_super_admin():
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


# Import statement fix
from src.models.models import Permission, PermissionSet
