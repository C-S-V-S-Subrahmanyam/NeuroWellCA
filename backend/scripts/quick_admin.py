#!/usr/bin/env python3
"""Quick admin account creation"""

import psycopg2
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect('postgresql://neurowellca_user:neurowellca_password_2026@postgres:5432/neurowellca_db')
cur = conn.cursor()

print("\n🔐 Creating admin account...")

# Delete if exists
cur.execute("DELETE FROM users WHERE username = 'admin'")
conn.commit()

hashed_password = pwd_context.hash("admin")

# Create admin
cur.execute("""
    INSERT INTO users (username, email, password_hash, full_name, has_completed_initial_assessment, email_verified, is_active, created_at, updated_at)
    VALUES ('admin', 'admin@gmail.com', %s, 'System Administrator', true, true, true, %s, %s)
    RETURNING id
""", (hashed_password, datetime.utcnow(), datetime.utcnow()))

admin_id = cur.fetchone()[0]
conn.commit()

# Get/Create super_admin role
cur.execute("SELECT id FROM roles WHERE code = 'super_admin'")
role = cur.fetchone()

if not role:
    cur.execute("""
        INSERT INTO roles (code, name, description, is_system, is_active, created_at)
        VALUES ('super_admin', 'Super Administrator', 'Full system access', true, true, %s)
        RETURNING id
    """, (datetime.utcnow(),))
    role_id = cur.fetchone()[0]
    
    # Assign all permission sets
    cur.execute("SELECT id FROM permission_sets")
    for (ps_id,) in cur.fetchall():
        cur.execute("""
            INSERT INTO role_permission_sets (role_id, permission_set_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (role_id, ps_id))
    conn.commit()
else:
    role_id = role[0]

# Assign role to admin
cur.execute("""
    INSERT INTO user_roles (user_id, role_id)
    VALUES (%s, %s) ON CONFLICT DO NOTHING
""", (admin_id, role_id))
conn.commit()

print(f"✅ Admin created!")
print(f"   Username: admin")
print(f"   Email: admin@gmail.com")
print(f"   Password: admin")

cur.close()
conn.close()
