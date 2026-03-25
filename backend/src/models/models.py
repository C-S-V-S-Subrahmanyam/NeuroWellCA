"""
SQLAlchemy models for all database tables
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.database import Base
import enum


class RiskLevel(str, enum.Enum):
    """Risk level enumeration"""
    LOW = "low"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


class SettingSegment(str, enum.Enum):
    """Settings segment enumeration"""
    AIML = "aiml"
    AUTH = "auth"


class ChangeType(str, enum.Enum):
    """Configuration change type"""
    CREATE = "create"
    UPDATE = "update"
    ROLLBACK = "rollback"


class FeedbackType(str, enum.Enum):
    """Feedback type enumeration"""
    POSITIVE = "positive"
    NEGATIVE = "negative"


class FeedbackStatus(str, enum.Enum):
    """Feedback status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class User(Base):
    """User model with RBAC support"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    full_name = Column(String(100))
    age = Column(Integer)
    guardian_contact = Column(String(20))
    guardian_email = Column(String(255))
    
    has_completed_initial_assessment = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Token versioning for invalidating all user tokens
    token_version = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))  # Soft delete
    
    # Relationships
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    crisis_logs = relationship("CrisisLog", back_populates="user", cascade="all, delete-orphan")
    guardian_alerts = relationship("GuardianAlert", back_populates="user", cascade="all, delete-orphan")
    game_progress = relationship("GameProgress", back_populates="user", cascade="all, delete-orphan")
    
    # RBAC relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    user_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserPermission.user_id")
    user_permission_sets = relationship("UserPermissionSet", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserPermissionSet.user_id")
    auth_identities = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")
    feedback_given = relationship("MessageFeedback", back_populates="user", cascade="all, delete-orphan", foreign_keys="MessageFeedback.user_id")


# RBAC Models

class Permission(Base):
    """Permission model - atomic authorization units"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'chat.view', 'assessment.create'
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # e.g., 'chat', 'assessment', 'user', 'admin'
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    permission_set_permissions = relationship("PermissionSetPermission", back_populates="permission", cascade="all, delete-orphan")
    user_permissions = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")


class PermissionSet(Base):
    """Permission set model - grouping of related permissions"""
    __tablename__ = "permission_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'crisis_responder', 'therapist'
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    permissions = relationship("PermissionSetPermission", back_populates="permission_set", cascade="all, delete-orphan")
    role_permission_sets = relationship("RolePermissionSet", back_populates="permission_set", cascade="all, delete-orphan")
    user_permission_sets = relationship("UserPermissionSet", back_populates="permission_set", cascade="all, delete-orphan")


class PermissionSetPermission(Base):
    """Junction table linking permission sets to permissions"""
    __tablename__ = "permission_set_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_set_id = Column(Integer, ForeignKey("permission_sets.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    permission_set = relationship("PermissionSet", back_populates="permissions")
    permission = relationship("Permission", back_populates="permission_set_permissions")


class Role(Base):
    """Role model - collection of permission sets"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'super_admin', 'therapist', 'patient'
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    permission_sets = relationship("RolePermissionSet", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class RolePermissionSet(Base):
    """Junction table linking roles to permission sets"""
    __tablename__ = "role_permission_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_set_id = Column(Integer, ForeignKey("permission_sets.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="permission_sets")
    permission_set = relationship("PermissionSet", back_populates="role_permission_sets")


class UserRole(Base):
    """Junction table for user-role assignments - supports multi-role"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")


class UserPermission(Base):
    """Direct permission assignment to users (bypassing roles)"""
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_permissions", foreign_keys=[user_id])
    permission = relationship("Permission", back_populates="user_permissions")


class UserPermissionSet(Base):
    """Direct permission set assignment to users (bypassing roles)"""
    __tablename__ = "user_permission_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission_set_id = Column(Integer, ForeignKey("permission_sets.id", ondelete="CASCADE"), nullable=False)
    
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_permission_sets", foreign_keys=[user_id])
    permission_set = relationship("PermissionSet", back_populates="user_permission_sets")


class RbacAuditLog(Base):
    """Audit log for RBAC changes"""
    __tablename__ = "rbac_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # 'user', 'role', 'permission', etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # 'create', 'update', 'delete', 'assign', 'revoke'
    
    old_value = Column(JSON)  # Previous state
    new_value = Column(JSON)  # New state
    
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ip_address = Column(String(45))
    user_agent = Column(Text)


# Auth Models

class AuthProvider(Base):
    """Auth provider configuration (Google, GitHub, etc.)"""
    __tablename__ = "auth_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 'google', 'github', 'microsoft', 'local'
    display_name = Column(String(100), nullable=False)
    
    is_enabled = Column(Boolean, default=True)
    config = Column(JSON)  # Provider-specific configuration
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    auth_identities = relationship("AuthIdentity", back_populates="provider", cascade="all, delete-orphan")


class AuthIdentity(Base):
    """Links users to auth providers (OAuth identities)"""
    __tablename__ = "auth_identities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(Integer, ForeignKey("auth_providers.id", ondelete="CASCADE"), nullable=False)
    
    provider_user_id = Column(String(255), nullable=False)  # User ID from provider
    provider_email = Column(String(255))
    provider_username = Column(String(255))
    
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    expires_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="auth_identities")
    provider = relationship("AuthProvider", back_populates="auth_identities")


class RevokedToken(Base):
    """Blacklisted JWT tokens"""
    __tablename__ = "revoked_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token = Column(Text, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    reason = Column(String(100))  # 'logout', 'password_change', 'admin_revoke'


class Assessment(Base):
    """Mental health assessment model"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # PHQ-9 Score (Depression: 0-27)
    phq9_score = Column(Integer, nullable=False)
    
    # GAD-7 Score (Anxiety: 0-21)
    gad7_score = Column(Integer, nullable=False)
    
    # Stress Level (0-10)
    stress_level = Column(Integer, nullable=False)
    
    # Combined Risk Assessment
    risk_level = Column(Enum(RiskLevel), nullable=False)
    
    # Individual PHQ-9 Answers (9 questions, 0-3 each)
    phq9_q1 = Column(Integer)
    phq9_q2 = Column(Integer)
    phq9_q3 = Column(Integer)
    phq9_q4 = Column(Integer)
    phq9_q5 = Column(Integer)
    phq9_q6 = Column(Integer)
    phq9_q7 = Column(Integer)
    phq9_q8 = Column(Integer)
    phq9_q9 = Column(Integer)
    
    # Individual GAD-7 Answers (7 questions, 0-3 each)
    gad7_q1 = Column(Integer)
    gad7_q2 = Column(Integer)
    gad7_q3 = Column(Integer)
    gad7_q4 = Column(Integer)
    gad7_q5 = Column(Integer)
    gad7_q6 = Column(Integer)
    gad7_q7 = Column(Integer)
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assessments")


class Conversation(Base):
    """Chat conversation model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(50), index=True)
    
    message_text = Column(Text, nullable=False)
    sender = Column(String(10), nullable=False)  # 'user' or 'ai'
    
    # Crisis detection
    crisis_detected = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    
    # Vector embedding ID in Qdrant
    vector_id = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")


class CrisisLog(Base):
    """Crisis detection log model"""
    __tablename__ = "crisis_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    message_text = Column(Text, nullable=False)
    crisis_score = Column(Integer, nullable=False)
    keywords_detected = Column(Text)  # JSON string of detected keywords
    
    action_taken = Column(String(50))  # 'guardian_alerted', 'resource_provided', etc.
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="crisis_logs")


class GuardianAlert(Base):
    """Guardian alert model for crisis situations"""
    __tablename__ = "guardian_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crisis_log_id = Column(Integer, ForeignKey("crisis_logs.id"))
    
    guardian_contact = Column(String(255), nullable=False)
    alert_sent = Column(Boolean, default=False)
    alert_method = Column(String(20))  # 'whatsapp', 'sms', 'email'
    
    message_sent = Column(Text)
    response_received = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="guardian_alerts")


class GameProgress(Base):
    """Gamification progress model"""
    __tablename__ = "games_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_games_progress_user_id"), nullable=False, unique=True)
    
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    conversations_count = Column(Integer, default=0)
    assessments_completed = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    
    badges = Column(Text)  # JSON string of earned badges
    
    last_activity = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="game_progress")


class ChatSession(Base):
    """Chat session metadata for LSTM summarization"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    
    title = Column(String(200))  # AI-generated title from LSTM
    summary = Column(Text)  # AI-generated summary
    
    message_count = Column(Integer, default=0)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")


# LLM Provider Model

class LlmProvider(Base):
    """LLM provider configuration (Anthropic, OpenAI, Ollama, etc.)"""
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(50), nullable=False)  # 'anthropic', 'openai', 'google', 'ollama', 'custom'
    
    base_url = Column(String(255))
    api_key_encrypted = Column(Text)  # Encrypted API key
    
    config = Column(JSON)  # Provider-specific configuration
    models = Column(JSON)  # Available models array
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Health check
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(20))  # 'healthy', 'unhealthy', 'unknown'
    health_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


# Feedback Models

class MessageFeedback(Base):
    """User feedback on AI responses"""
    __tablename__ = "message_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    feedback_type = Column(Enum(FeedbackType), nullable=False)  # 'positive' or 'negative'
    reason = Column(Text)  # Optional user comment
    
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.PENDING)  # 'pending', 'approved', 'rejected', 'dismissed'
    
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="feedback_given", foreign_keys=[user_id])
    conversation = relationship("Conversation")


class GoldenExample(Base):
    """Admin-curated ideal responses for RAG learning"""
    __tablename__ = "golden_examples"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)  # User input
    response = Column(Text, nullable=False)  # Ideal AI response
    
    category = Column(String(100))  # 'crisis', 'anxiety', 'depression', 'general'
    tags = Column(JSON)  # Array of tags
    
    source_feedback_id = Column(Integer, ForeignKey("message_feedback.id"))  # If created from feedback
    
    qdrant_point_id = Column(String(50))  # Vector DB reference
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority examples used first
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


# Settings Model Enhancement (add to existing Settings model or create new)

class Setting(Base):
    """Application settings with version control and audit trail"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, nullable=False, unique=True)  # Incrementing version number
    
    # AI/ML Settings
    ai_model = Column(String(100), default="llama3.2:3b")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    top_p = Column(Float, default=0.9)
    deny_words = Column(JSON)  # Array of words to filter
    
    # LLM Provider
    provider_id = Column(Integer, ForeignKey("llm_providers.id"))
    allow_user_model_selection = Column(Boolean, default=False)  # Let users choose models
    
    # Auth Settings
    auth_enabled = Column(Boolean, default=True)
    oauth_google_enabled = Column(Boolean, default=False)
    oauth_github_enabled = Column(Boolean, default=False)
    oauth_microsoft_enabled = Column(Boolean, default=False)
    
    # Feedback Settings
    feedback_auto_approve_positive = Column(Boolean, default=True)
    feedback_auto_approve_negative = Column(Boolean, default=False)
    feedback_require_reason_positive = Column(Boolean, default=False)
    feedback_require_reason_negative = Column(Boolean, default=True)
    
    # Crisis Detection
    crisis_threshold = Column(Integer, default=70)
    crisis_alert_enabled = Column(Boolean, default=True)
    
    # Audit trail fields
    change_type = Column(Enum(ChangeType), default=ChangeType.CREATE)  # 'create', 'update', 'rollback'
    source_version_id = Column(Integer, ForeignKey("settings.id"))  # Previous version
    target_version_id = Column(Integer, ForeignKey("settings.id"))  # Target for rollback
    change_reason = Column(Text)  # Why this change was made
    
    is_active = Column(Boolean, default=False)  # Only one active version
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime(timezone=True))

