"""Seed RBAC data with mental health-specific permissions

Revision ID: 002_seed_rbac_data
Revises: 001_rbac_tables
Create Date: 2026-02-19 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '002_seed_rbac_data'
down_revision: Union[str, None] = '001_rbac_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mental health-specific permissions organized by category
    permissions_data = [
        # Chat permissions
        ('chat.view', 'View Chat', 'Can view chat messages', 'chat'),
        ('chat.create', 'Create Chat', 'Can send chat messages', 'chat'),
        ('chat.history', 'Chat History', 'Can view chat history', 'chat'),
        ('chat.delete', 'Delete Chat', 'Can delete chat messages', 'chat'),
        ('chat.export', 'Export Chat', 'Can export chat history', 'chat'),
        
        # Assessment permissions
        ('assessment.view', 'View Assessment', 'Can view mental health assessments', 'assessment'),
        ('assessment.create', 'Create Assessment', 'Can create assessments (PHQ-9, GAD-7)', 'assessment'),
        ('assessment.edit', 'Edit Assessment', 'Can edit assessment responses', 'assessment'),
        ('assessment.delete', 'Delete Assessment', 'Can delete assessments', 'assessment'),
        ('assessment.view_others', 'View Others\' Assessments', 'Can view other users\' assessments', 'assessment'),
        
        # Crisis management permissions
        ('crisis.view', 'View Crisis', 'Can view crisis logs', 'crisis'),
        ('crisis.respond', 'Respond to Crisis', 'Can respond to crisis situations', 'crisis'),
        ('crisis.alert_guardian', 'Alert Guardian', 'Can trigger guardian alerts', 'crisis'),
        ('crisis.manage', 'Manage Crisis', 'Full crisis management access', 'crisis'),
        
        # User management permissions
        ('user.view', 'View Users', 'Can view user profiles', 'user'),
        ('user.edit', 'Edit Users', 'Can edit user information', 'user'),
        ('user.delete', 'Delete Users', 'Can delete users', 'user'),
        ('user.manage_roles', 'Manage User Roles', 'Can assign/remove roles from users', 'user'),
        
        # Role & permission management
        ('role.view', 'View Roles', 'Can view roles', 'role'),
        ('role.create', 'Create Roles', 'Can create new roles', 'role'),
        ('role.edit', 'Edit Roles', 'Can edit role definitions', 'role'),
        ('role.delete', 'Delete Roles', 'Can delete roles', 'role'),
        ('permission.view', 'View Permissions', 'Can view permissions', 'permission'),
        ('permission.manage', 'Manage Permissions', 'Can manage permission sets', 'permission'),
        
        # Settings & configuration
        ('settings.view', 'View Settings', 'Can view application settings', 'settings'),
        ('settings.edit', 'Edit Settings', 'Can edit settings', 'settings'),
        ('settings.history', 'View Settings History', 'Can view configuration history', 'settings'),
        ('settings.rollback', 'Rollback Settings', 'Can rollback to previous settings', 'settings'),
        
        # Feedback & quality
        ('feedback.view', 'View Feedback', 'Can view user feedback', 'feedback'),
        ('feedback.submit', 'Submit Feedback', 'Can submit feedback on AI responses', 'feedback'),
        ('feedback.manage', 'Manage Feedback', 'Can review and manage feedback', 'feedback'),
        ('feedback.golden_examples', 'Manage Golden Examples', 'Can create golden response examples', 'feedback'),
        
        # AI/ML management
        ('ai.view_provider', 'View AI Provider', 'Can view AI provider settings', 'ai'),
        ('ai.manage_provider', 'Manage AI Provider', 'Can configure AI providers', 'ai'),
        ('ai.select_model', 'Select Model', 'Can choose which AI model to use', 'ai'),
        
        # System & audit
        ('system.view_logs', 'View System Logs', 'Can view system audit logs', 'system'),
        ('system.manage', 'Manage System', 'Full system administration', 'system'),
    ]
    
    # Insert permissions
    conn = op.get_bind()
    for code, name, description, category in permissions_data:
        conn.execute(
            sa.text("""
                INSERT INTO permissions (code, name, description, category, is_active, created_at)
                VALUES (:code, :name, :description, :category, true, :created_at)
            """),
            {"code": code, "name": name, "description": description, "category": category, "created_at": datetime.now()}
        )
    
    # Mental health-specific permission sets
    permission_sets_data = [
        ('super_admin', 'Super Administrator', 'Full system access - all permissions'),
        ('therapist_manager', 'Therapist Manager', 'Therapist with full patient management'),
        ('crisis_responder', 'Crisis Responder', 'Crisis intervention specialist'),
        ('chat_advanced', 'Advanced Chat User', 'Enhanced chat with AI model selection'),
        ('chat_basic', 'Basic Chat User', 'Basic chat functionality'),
        ('assessment_manager', 'Assessment Manager', 'Manage mental health assessments'),
        ('feedback_reviewer', 'Feedback Reviewer', 'Review and curate feedback'),
        ('settings_manager', 'Settings Manager', 'Configure application settings'),
    ]
    
    # Insert permission sets
    for code, name, description in permission_sets_data:
        conn.execute(
            sa.text("""
                INSERT INTO permission_sets (code, name, description, is_active, created_at)
                VALUES (:code, :name, :description, true, :created_at)
            """),
            {"code": code, "name": name, "description": description, "created_at": datetime.now()}
        )
    
    # Map permissions to permission sets
    permission_set_mappings = {
        'super_admin': [
            'chat.view', 'chat.create', 'chat.history', 'chat.delete', 'chat.export',
            'assessment.view', 'assessment.create', 'assessment.edit', 'assessment.delete', 'assessment.view_others',
            'crisis.view', 'crisis.respond', 'crisis.alert_guardian', 'crisis.manage',
            'user.view', 'user.edit', 'user.delete', 'user.manage_roles',
            'role.view', 'role.create', 'role.edit', 'role.delete',
            'permission.view', 'permission.manage',
            'settings.view', 'settings.edit', 'settings.history', 'settings.rollback',
            'feedback.view', 'feedback.submit', 'feedback.manage', 'feedback.golden_examples',
            'ai.view_provider', 'ai.manage_provider', 'ai.select_model',
            'system.view_logs', 'system.manage'
        ],
        'therapist_manager': [
            'chat.view', 'chat.create', 'chat.history', 'chat.export',
            'assessment.view', 'assessment.create', 'assessment.edit', 'assessment.view_others',
            'crisis.view', 'crisis.respond', 'crisis.alert_guardian', 'crisis.manage',
            'user.view', 'user.edit',
            'feedback.view', 'feedback.submit', 'feedback.manage',
            'ai.select_model'
        ],
        'crisis_responder': [
            'chat.view', 'chat.create', 'chat.history',
            'assessment.view', 'assessment.view_others',
            'crisis.view', 'crisis.respond', 'crisis.alert_guardian', 'crisis.manage',
            'feedback.submit'
        ],
        'chat_advanced': [
            'chat.view', 'chat.create', 'chat.history', 'chat.export',
            'assessment.view', 'assessment.create',
            'feedback.submit',
            'ai.select_model'
        ],
        'chat_basic': [
            'chat.view', 'chat.create', 'chat.history',
            'assessment.view', 'assessment.create',
            'feedback.submit'
        ],
        'assessment_manager': [
            'assessment.view', 'assessment.create', 'assessment.edit', 'assessment.delete', 'assessment.view_others',
            'feedback.submit'
        ],
        'feedback_reviewer': [
            'feedback.view', 'feedback.submit', 'feedback.manage', 'feedback.golden_examples',
            'chat.view', 'chat.history'
        ],
        'settings_manager': [
            'settings.view', 'settings.edit', 'settings.history', 'settings.rollback',
            'ai.view_provider', 'ai.manage_provider',
            'system.view_logs'
        ]
    }
    
    # Link permissions to permission sets
    for set_code, perm_codes in permission_set_mappings.items():
        for perm_code in perm_codes:
            conn.execute(
                sa.text("""
                    INSERT INTO permission_set_permissions (permission_set_id, permission_id, created_at)
                    SELECT ps.id, p.id, :created_at
                    FROM permission_sets ps, permissions p
                    WHERE ps.code = :set_code AND p.code = :perm_code
                """),
                {"set_code": set_code, "perm_code": perm_code, "created_at": datetime.now()}
            )
    
    # Mental health-specific roles
    roles_data = [
        ('super_admin', 'Super Administrator', 'Complete system access for administrators', True),
        ('therapist', 'Licensed Therapist', 'Mental health professional with patient management', True),
        ('crisis_specialist', 'Crisis Specialist', 'Specialized in crisis intervention', True),
        ('patient_advanced', 'Advanced Patient', 'Patient with enhanced chat features', True),
        ('patient', 'Patient', 'Standard patient with basic features', True),
        ('guardian', 'Guardian/Caregiver', 'Parent or caregiver monitoring patient', True),
        ('researcher', 'Researcher', 'Research access to anonymized data', True),
    ]
    
    # Insert roles
    for code, name, description, is_system in roles_data:
        conn.execute(
            sa.text("""
                INSERT INTO roles (code, name, description, is_system, is_active, created_at)
                VALUES (:code, :name, :description, :is_system, true, :created_at)
            """),
            {"code": code, "name": name, "description": description, "is_system": is_system, "created_at": datetime.now()}
        )
    
    # Map permission sets to roles
    role_permission_set_mappings = {
        'super_admin': ['super_admin'],
        'therapist': ['therapist_manager', 'assessment_manager', 'feedback_reviewer'],
        'crisis_specialist': ['crisis_responder', 'chat_advanced'],
        'patient_advanced': ['chat_advanced', 'assessment_manager'],
        'patient': ['chat_basic'],
        'guardian': ['chat_basic', 'assessment_manager'],  # Can monitor patient
        'researcher': ['assessment_manager', 'feedback_reviewer']  # Read-only research access
    }
    
    # Link permission sets to roles
    for role_code, set_codes in role_permission_set_mappings.items():
        for set_code in set_codes:
            conn.execute(
                sa.text("""
                    INSERT INTO role_permission_sets (role_id, permission_set_id, created_at)
                    SELECT r.id, ps.id, :created_at
                    FROM roles r, permission_sets ps
                    WHERE r.code = :role_code AND ps.code = :set_code
                """),
                {"role_code": role_code, "set_code": set_code, "created_at": datetime.now()}
            )


def downgrade() -> None:
    conn = op.get_bind()
    
    # Delete in reverse order due to foreign keys
    conn.execute(sa.text("DELETE FROM role_permission_sets"))
    conn.execute(sa.text("DELETE FROM permission_set_permissions"))
    conn.execute(sa.text("DELETE FROM roles"))
    conn.execute(sa.text("DELETE FROM permission_sets"))
    conn.execute(sa.text("DELETE FROM permissions"))
