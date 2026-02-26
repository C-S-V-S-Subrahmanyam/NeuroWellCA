"""Complete RBAC setup"""
from sqlalchemy import create_engine, text
from datetime import datetime

DB_URL = "postgresql://neurowellca_user:neurowellca_password_2026@neurowellca-postgres:5432/neurowellca_db"

engine = create_engine(DB_URL)
conn = engine.connect()

try:
    # Create patient role if not exists
    result = conn.execute(text("SELECT id FROM roles WHERE code='patient'"))
    patient_role = result.scalar()
    
    if not patient_role:
        print("Creating patient role...")
        conn.execute(text("""
            INSERT INTO roles (code, name, description, is_system, is_active, created_at)
            VALUES ('patient', 'Patient', 'Standard patient with basic features', false, true, :now)
        """), {"now": datetime.now()})
        conn.commit()
        patient_role = conn.execute(text("SELECT id FROM roles WHERE code='patient'")).scalar()
        print(f"✅ Created patient role (ID: {patient_role})")
    else:
        print(f"✓ Patient role already exists (ID: {patient_role})")
    
    # Link to chat_basic permission set
    chat_basic_id = conn.execute(text("SELECT id FROM permission_sets WHERE code='chat_basic'")).scalar()
    
    if chat_basic_id:
        # Check if already linked
        existing = conn.execute(text("""
            SELECT id FROM role_permission_sets 
            WHERE role_id=:r AND permission_set_id=:ps
        """), {"r": patient_role, "ps": chat_basic_id}).scalar()
        
        if not existing:
            conn.execute(text("""
                INSERT INTO role_permission_sets (role_id, permission_set_id)
                VALUES (:r, :ps)
            """), {"r": patient_role, "ps": chat_basic_id})
            conn.commit()
            print(f"✅ Linked patient role to chat_basic permission set")
        else:
            print("✓ Already linked to chat_basic")
    
    # Assign role to all existing users
    print("\nAssigning patient role to existing users...")
    users = conn.execute(text("SELECT id, username FROM users WHERE is_active=true AND deleted_at IS NULL")).fetchall()
    
    fixed = 0
    for user_id, username in users:
        # Check if already has role
        existing = conn.execute(text("""
            SELECT id FROM user_roles 
            WHERE user_id=:u AND role_id=:r
        """), {"u": user_id, "r": patient_role}).scalar()
        
        if not existing:
            conn.execute(text("""
                INSERT INTO user_roles (user_id, role_id, assigned_at)
                VALUES (:u, :r, :now)
            """), {"u": user_id, "r": patient_role, "now": datetime.now()})
            conn.commit()
            print(f"  ✅ Assigned patient role to '{username}'")
            fixed += 1
        else:
            print(f"  ✓ '{username}' already has patient role")
    
    print(f"\n🎉 Complete! Fixed {fixed} user(s)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
    engine.dispose()
