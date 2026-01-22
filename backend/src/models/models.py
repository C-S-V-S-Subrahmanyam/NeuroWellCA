"""
SQLAlchemy models for all database tables
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
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


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    full_name = Column(String(100))
    age = Column(Integer)
    guardian_contact = Column(String(20))
    
    has_completed_initial_assessment = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    crisis_logs = relationship("CrisisLog", back_populates="user", cascade="all, delete-orphan")
    guardian_alerts = relationship("GuardianAlert", back_populates="user", cascade="all, delete-orphan")
    game_progress = relationship("GameProgress", back_populates="user", cascade="all, delete-orphan")


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
    
    guardian_contact = Column(String(20), nullable=False)
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
