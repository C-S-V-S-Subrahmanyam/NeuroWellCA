#!/usr/bin/env python3
"""Verify user permissions are properly set up"""

import psycopg2

# Connect to database
conn = psycopg2.connect(
    'postgresql://neurowellca_user:neurowellca_password_2026@postgres:5432/neurowellca_db'
)
cur = conn.cursor()

print("\n" + "="*80)
print("🔍 USER PERMISSIONS VERIFICATION")
print("="*80)

# Check users and their roles
cur.execute("""
    SELECT u.id, u.username, u.email, u.is_active
    FROM users u
    WHERE u.deleted_at IS NULL
    ORDER BY u.id
""")
users = cur.fetchall()

print(f"\n📊 Total Users: {len(users)}")
print("-" * 80)

for user_id, username, email, is_active in users:
    status = "✅ Active" if is_active else "❌ Inactive"
    print(f"\n👤 User #{user_id}: {username} ({email}) - {status}")
    
    # Get roles
    cur.execute("""
        SELECT r.id, r.name, r.code
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = %s
    """, (user_id,))
    roles = cur.fetchall()
    
    if roles:
        for role_id, role_name, role_code in roles:
            print(f"   🎭 Role: {role_name} (code: {role_code}, id: {role_id})")
    else:
        print(f"   ⚠️  NO ROLES ASSIGNED!")
    
    # Get effective permissions
    cur.execute("""
        SELECT DISTINCT p.code, p.name
        FROM user_roles ur
        JOIN role_permission_sets rps ON ur.role_id = rps.role_id
        JOIN permission_set_permissions psp ON rps.permission_set_id = psp.permission_set_id
        JOIN permissions p ON psp.permission_id = p.id
        WHERE ur.user_id = %s
        ORDER BY p.code
    """, (user_id,))
    permissions = cur.fetchall()
    
    if permissions:
        print(f"   🔐 Effective Permissions ({len(permissions)}):")
        for perm_code, perm_name in permissions:
            print(f"      • {perm_code}: {perm_name}")
    else:
        print(f"   ⚠️  NO EFFECTIVE PERMISSIONS!")

# Show RBAC summary
print("\n" + "="*80)
print("📋 RBAC SYSTEM SUMMARY")
print("="*80)

cur.execute("SELECT COUNT(*) FROM permissions")
perm_count = cur.fetchone()[0]
print(f"✅ Permissions: {perm_count}")

cur.execute("SELECT COUNT(*) FROM permission_sets")
ps_count = cur.fetchone()[0]
print(f"✅ Permission Sets: {ps_count}")

cur.execute("SELECT COUNT(*) FROM roles WHERE deleted_at IS NULL")
role_count = cur.fetchone()[0]
print(f"✅ Roles: {role_count}")

cur.execute ("SELECT COUNT(*) FROM user_roles")
ur_count = cur.fetchone()[0]
print(f"✅ User-Role Assignments: {ur_count}")

print("\n" + "="*80)
print("✅ Verification Complete!")
print("="*80 + "\n")

cur.close()
conn.close()
