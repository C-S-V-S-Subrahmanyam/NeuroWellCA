"""
Manually run the RBAC seed data (since tables already exist)
"""
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://neurowellca_user:neurowellca_password_2026@neurowellca-postgres:5432/neurowellca_db"

def seed_rbac_data():
    print("=== Seeding RBAC Data ===\n")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if data already exists
        result = conn.execute(text("SELECT COUNT(*) FROM permissions"))
        perm_count = result.scalar()
        
        if perm_count > 0:
            print(f"⚠️  Permissions already exist ({perm_count} found). Skipping seed.")
            return
        
        print("📝 Inserting permissions...")
        
        # Permissions data
        permissions = [
            # Chat
            ('chat.view', 'View Chat', 'Can view chat messages', 'chat'),
            ('chat.create', 'Create Chat', 'Can send chat messages', 'chat'),
            ('chat.history', 'Chat History', 'Can view chat history', 'chat'),
            ('chat.delete', 'Delete Chat', 'Can delete chat messages', 'chat'),
            ('chat.export', 'Export Chat', 'Can export chat history', 'chat'),
            # Assessment
            ('assessment.view', 'View Assessment', 'Can view mental health assessments', 'assessment'),
            ('assessment.create', 'Create Assessment', 'Can create assessments', 'assessment'),
            ('assessment.edit', 'Edit Assessment', 'Can edit assessment responses', 'assessment'),
            ('assessment.delete', 'Delete Assessment', 'Can delete assessments', 'assessment'),
            # Crisis
            ('crisis.view', 'View Crisis', 'Can view crisis logs', 'crisis'),
            ('crisis.respond', 'Respond to Crisis', 'Can respond to crisis', 'crisis'),
            # User
            ('user.view', 'View Users', 'Can view user profiles', 'user'),
            # Feedback
            ('feedback.view', 'View Feedback', 'Can view feedback', 'feedback'),
            ('feedback.submit', 'Submit Feedback', 'Can submit feedback', 'feedback'),
        ]
        
        for code, name, desc, cat in permissions:
            conn.execute(
                text("""INSERT INTO permissions (code, name, description, category, is_active, created_at)
                        VALUES (:code, :name, :desc, :cat, true, :now)"""),
                {"code": code, "name": name, "desc": desc, "cat": cat, "now": datetime.now()}
            )
            conn.commit()
        
        print(f"  ✅ Inserted {len(permissions)} permissions\n")
        
        print("📦 Creating permission sets...")
        
        # Permission sets
        sets = [
            ('chat_basic', 'Basic Chat User', 'Basic chat functionality'),
            ('assessment_manager', 'Assessment Manager', 'Manage mental health assessments'),
        ]
        
        for code, name, desc in sets:
            conn.execute(
                text("""INSERT INTO permission_sets (code, name, description, is_active, created_at)
                        VALUES (:code, :name, :desc, true, :now)"""),
                {"code": code, "name": name, "desc": desc, "now": datetime.now()}
            )
            conn.commit()
        
        print(f"  ✅ Inserted {len(sets)} permission sets\n")
        
        # Get IDs for linking
        chat_basic_id = conn.execute(text("SELECT id FROM permission_sets WHERE code='chat_basic'")).scalar()
        assess_mgr_id = conn.execute(text("SELECT id FROM permission_sets WHERE code='assessment_manager'")).scalar()
        
        # Link permissions to sets
        print("🔗 Linking permissions to sets...")
        
        # chat_basic permissions
        chat_perms = ['chat.view', 'chat.create', 'chat.history', 'assessment.view', 'assessment.create', 'feedback.submit']
        for perm_code in chat_perms:
            perm_id = conn.execute(text(f"SELECT id FROM permissions WHERE code='{perm_code}'")).scalar()
            if perm_id:
                conn.execute(
                    text("""INSERT INTO permission_set_permissions (permission_set_id, permission_id)
                            VALUES (:ps_id, :p_id)"""),
                    {"ps_id": chat_basic_id, "p_id": perm_id}
                )
                conn.commit()
        
        print("  ✅ Linked chat_basic permissions\n")
        
        # Create roles
        print("👥 Creating roles...")
        
        roles = [
            ('patient', 'Patient', 'Standard patient with basic features', False, False),
            ('super_admin', 'Super Administrator', 'Full system access', True, False),
        ]
        
        for code, name, desc, is_sys, is_def in roles:
            conn.execute(
                text("""INSERT INTO roles (code, name, description, is_system, is_default, is_active, created_at)
                        VALUES (:code, :name, :desc, :sys, :def, true, :now)"""),
                {"code": code, "name": name, "desc": desc, "sys": is_sys, "def": is_def, "now": datetime.now()}
            )
            conn.commit()
        
        print(f"  ✅ Inserted {len(roles)} roles\n")
        
        # Link patient role to chat_basic permission set
        patient_role_id = conn.execute(text("SELECT id FROM roles WHERE code='patient'")).scalar()
        
        conn.execute(
            text("""INSERT INTO role_permission_sets (role_id, permission_set_id)
                    VALUES (:r_id, :ps_id)"""),
            {"r_id": patient_role_id, "ps_id": chat_basic_id}
        )
        conn.commit()
        
        print("  ✅ Linked patient role to permission sets\n")
        
        print("🎉 RBAC seed complete!\n")

if __name__ == "__main__":
    seed_rbac_data()
