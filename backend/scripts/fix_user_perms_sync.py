"""
Quick fix for existing users who don't have permissions
Run this with: docker exec -it neurowellca-backend python scripts/fix_user_perms_sync.py
"""
import sys
import os

# Add parent directory to path for imports  
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# Import models
from src.models.models import User, Role, UserRole

# Database URL (using synchronous driver)
DATABASE_URL = "postgresql://neurowellca_user:neurowellca_password_2026@neurowellca-postgres:5432/neurowellca_db"

def fix_permissions():
    print("=== NeuroWell CA - Fix User Permissions ===\n")
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Get all active users
        users = db.query(User).filter(
            User.is_active == True,
            User.deleted_at == None
        ).all()
        
        # Get patient role
        patient_role = db.query(Role).filter(Role.code == "patient").first()
        
        if not patient_role:
            print("❌ 'patient' role not found!")
            return
        
        print(f"🔍 Found {len(users)} active users")
        print(f"📋 Default role: {patient_role.name} (ID: {patient_role.id})\n")
        
        fixed_count = 0
        
        for user in users:
            # Check if user already has this role
            existing = db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == patient_role.id
            ).first()
            
            if existing:
                print(f"  ✓ User '{user.username}' already has 'patient' role")
            else:
                # Assign patient role
                user_role = UserRole(
                    user_id=user.id,
                    role_id=patient_role.id,
                    assigned_at=datetime.now()
                )
                db.add(user_role)
                db.commit()
                print(f"  ✅ Assigned 'patient' role to user '{user.username}'")
                fixed_count += 1
        
        print(f"\n🎉 Fixed {fixed_count} user(s)")
        print("✅ All users now have proper permissions!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    fix_permissions()
