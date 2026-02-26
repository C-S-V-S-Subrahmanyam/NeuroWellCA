"""
Fix permissions for existing users who don't have the default 'patient' role assigned
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.models import User, Role, UserRole
from src.services.permission_service import PermissionService
from src.utils.config import settings

async def fix_user_permissions():
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Get all users
            result = await db.execute(select(User).where(User.is_active == True, User.deleted_at == None))
            users = result.scalars().all()
            
            # Get the patient role
            result = await db.execute(select(Role).where(Role.code == "patient"))
            patient_role = result.scalar_one_or_none()
            
            if not patient_role:
                print("❌ 'patient' role not found in database")
                return
            
            print(f"\n🔍 Found {len(users)} active users")
            print(f"📋 Default role: {patient_role.name} (ID: {patient_role.id})\n")
            
            fixed_count = 0
            
            for user in users:
                # Check if user already has this role
                result = await db.execute(
                    select(UserRole).where(
                        UserRole.user_id == user.id,
                        UserRole.role_id == patient_role.id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"  ✓ User '{user.username}' already has 'patient' role")
                else:
                    # Assign patient role
                    success = await PermissionService.assign_role_to_user(
                        db=db,
                        user_id=user.id,
                        role_id=patient_role.id
                    )
                    
                    if success:
                        print(f"  ✅ Assigned 'patient' role to user '{user.username}'")
                        fixed_count += 1
                    else:
                        print(f"  ❌ Failed to assign role to user '{user.username}'")
            
            print(f"\n🎉 Fixed {fixed_count} user(s)")
            print(f"✅ All users now have proper permissions!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("=== NeuroWell CA - Fix User Permissions ===\n")
    asyncio.run(fix_user_permissions())
