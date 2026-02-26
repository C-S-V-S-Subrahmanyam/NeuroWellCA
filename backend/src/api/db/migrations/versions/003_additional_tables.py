"""Add auth providers, feedback, LLM providers, and enhanced settings

Revision ID: 003_additional_tables
Revises: 002_seed_rbac_data
Create Date: 2026-02-19 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_additional_tables'
down_revision: Union[str, None] = '002_seed_rbac_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create auth_providers table
    op.create_table('auth_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_providers_id'), 'auth_providers', ['id'], unique=False)
    op.create_index(op.f('ix_auth_providers_name'), 'auth_providers', ['name'], unique=True)
    
    # Create auth_identities table
    op.create_table('auth_identities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('provider_user_id', sa.String(length=255), nullable=False),
        sa.Column('provider_email', sa.String(length=255), nullable=True),
        sa.Column('provider_username', sa.String(length=255), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['auth_providers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_identities_id'), 'auth_identities', ['id'], unique=False)
    
    # Create revoked_tokens table
    op.create_table('revoked_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revoked_tokens_id'), 'revoked_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)
    
    # Create llm_providers table
    op.create_table('llm_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('models', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(length=20), nullable=True),
        sa.Column('health_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_providers_id'), 'llm_providers', ['id'], unique=False)
    op.create_index(op.f('ix_llm_providers_name'), 'llm_providers', ['name'], unique=True)
    
    # Create message_feedback table
    op.create_table('message_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.Enum('POSITIVE', 'NEGATIVE', name='feedbacktype'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'DISMISSED', name='feedbackstatus'), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_feedback_id'), 'message_feedback', ['id'], unique=False)
    
    # Create golden_examples table
    op.create_table('golden_examples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('source_feedback_id', sa.Integer(), nullable=True),
        sa.Column('qdrant_point_id', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['source_feedback_id'], ['message_feedback.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_golden_examples_id'), 'golden_examples', ['id'], unique=False)
    
    # Create settings table with version control
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('top_p', sa.Float(), nullable=True),
        sa.Column('deny_words', sa.JSON(), nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('allow_user_model_selection', sa.Boolean(), nullable=True),
        sa.Column('auth_enabled', sa.Boolean(), nullable=True),
        sa.Column('oauth_google_enabled', sa.Boolean(), nullable=True),
        sa.Column('oauth_github_enabled', sa.Boolean(), nullable=True),
        sa.Column('oauth_microsoft_enabled', sa.Boolean(), nullable=True),
        sa.Column('feedback_auto_approve_positive', sa.Boolean(), nullable=True),
        sa.Column('feedback_auto_approve_negative', sa.Boolean(), nullable=True),
        sa.Column('feedback_require_reason_positive', sa.Boolean(), nullable=True),
        sa.Column('feedback_require_reason_negative', sa.Boolean(), nullable=True),
        sa.Column('crisis_threshold', sa.Integer(), nullable=True),
        sa.Column('crisis_alert_enabled', sa.Boolean(), nullable=True),
        sa.Column('change_type', sa.Enum('CREATE', 'UPDATE', 'ROLLBACK', name='changetype'), nullable=True),
        sa.Column('source_version_id', sa.Integer(), nullable=True),
        sa.Column('target_version_id', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], ),
        sa.ForeignKeyConstraint(['source_version_id'], ['settings.id'], ),
        sa.ForeignKeyConstraint(['target_version_id'], ['settings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_id'), 'settings', ['id'], unique=False)
    op.create_index(op.f('ix_settings_version'), 'settings', ['version'], unique=True)
    
    # Insert default settings
    op.execute("""
        INSERT INTO settings (
            version, ai_model, temperature, max_tokens, top_p, 
            deny_words, allow_user_model_selection,
            auth_enabled, oauth_google_enabled, oauth_github_enabled, oauth_microsoft_enabled,
            feedback_auto_approve_positive, feedback_auto_approve_negative,
            feedback_require_reason_positive, feedback_require_reason_negative,
            crisis_threshold, crisis_alert_enabled,
            change_type, is_active, created_at, activated_at
        ) VALUES (
            1, 'llama3.2:3b', 0.7, 2000, 0.9,
            '[]'::json, false,
            true, false, false, false,
            true, false,
            false, true,
            70, true,
            'CREATE', true, NOW(), NOW()
        )
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_settings_version'), table_name='settings')
    op.drop_index(op.f('ix_settings_id'), table_name='settings')
    op.drop_table('settings')
    
    op.drop_index(op.f('ix_golden_examples_id'), table_name='golden_examples')
    op.drop_table('golden_examples')
    
    op.drop_index(op.f('ix_message_feedback_id'), table_name='message_feedback')
    op.drop_table('message_feedback')
    
    op.drop_index(op.f('ix_llm_providers_name'), table_name='llm_providers')
    op.drop_index(op.f('ix_llm_providers_id'), table_name='llm_providers')
    op.drop_table('llm_providers')
    
    op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_id'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
    
    op.drop_index(op.f('ix_auth_identities_id'), table_name='auth_identities')
    op.drop_table('auth_identities')
    
    op.drop_index(op.f('ix_auth_providers_name'), table_name='auth_providers')
    op.drop_index(op.f('ix_auth_providers_id'), table_name='auth_providers')
    op.drop_table('auth_providers')
    
    # Drop enums
    sa.Enum(name='changetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='feedbackstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='feedbacktype').drop(op.get_bind(), checkfirst=True)
