"""Initial migration - Create all RBAC tables

Revision ID: 001_rbac_tables
Revises: 
Create Date: 2026-02-19 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_rbac_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    
    # Create permission_sets table
    op.create_table('permission_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_sets_code'), 'permission_sets', ['code'], unique=True)
    op.create_index(op.f('ix_permission_sets_id'), 'permission_sets', ['id'], unique=False)
    
    # Create permission_set_permissions junction table
    op.create_table('permission_set_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('permission_set_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_set_id'], ['permission_sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_set_permissions_id'), 'permission_set_permissions', ['id'], unique=False)
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_code'), 'roles', ['code'], unique=True)
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    
    # Create role_permission_sets junction table
    op.create_table('role_permission_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_set_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['permission_set_id'], ['permission_sets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_permission_sets_id'), 'role_permission_sets', ['id'], unique=False)
    
    # Update users table with RBAC fields
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True))
    op.add_column('users', sa.Column('token_version', sa.Integer(), server_default='1', nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create user_roles junction table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    
    # Create user_permissions (direct permissions)
    op.create_table('user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_permissions_id'), 'user_permissions', ['id'], unique=False)
    
    # Create user_permission_sets (direct permission sets)
    op.create_table('user_permission_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_set_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_set_id'], ['permission_sets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_permission_sets_id'), 'user_permission_sets', ['id'], unique=False)
    
    # Create rbac_audit_logs
    op.create_table('rbac_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rbac_audit_logs_id'), 'rbac_audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rbac_audit_logs_id'), table_name='rbac_audit_logs')
    op.drop_table('rbac_audit_logs')
    
    op.drop_index(op.f('ix_user_permission_sets_id'), table_name='user_permission_sets')
    op.drop_table('user_permission_sets')
    
    op.drop_index(op.f('ix_user_permissions_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    
    op.drop_index(op.f('ix_user_roles_id'), table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'token_version')
    op.drop_column('users', 'is_active')
    
    op.drop_index(op.f('ix_role_permission_sets_id'), table_name='role_permission_sets')
    op.drop_table('role_permission_sets')
    
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_index(op.f('ix_roles_code'), table_name='roles')
    op.drop_table('roles')
    
    op.drop_index(op.f('ix_permission_set_permissions_id'), table_name='permission_set_permissions')
    op.drop_table('permission_set_permissions')
    
    op.drop_index(op.f('ix_permission_sets_id'), table_name='permission_sets')
    op.drop_index(op.f('ix_permission_sets_code'), table_name='permission_sets')
    op.drop_table('permission_sets')
    
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_table('permissions')
