from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for authentication and profile management"""
    
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Profile fields (optional)
    is_anonymous = db.Column(db.Boolean, default=False)
    profile_name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    college = db.Column(db.String(200), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    
    # Guardian alert settings
    guardian_phone = db.Column(db.String(15), nullable=True)
    guardian_consent = db.Column(db.Boolean, default=False)
    
    # Assessment tracking
    has_completed_initial_assessment = db.Column(db.Boolean, default=False)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    crisis_logs = db.relationship('CrisisLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    guardian_alerts = db.relationship('GuardianAlert', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    games_progress = db.relationship('GameProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'profile_name': self.profile_name,
            'age': self.age,
            'college': self.college,
            'major': self.major,
            'is_anonymous': self.is_anonymous,
            'guardian_consent': self.guardian_consent,
            'has_completed_initial_assessment': self.has_completed_initial_assessment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Assessment(db.Model):
    """Assessment model for PHQ-9, GAD-7, and stress scores"""
    
    __tablename__ = 'assessments'
    
    assessment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Scores
    phq9_score = db.Column(db.Integer, nullable=False)  # 0-27
    gad7_score = db.Column(db.Integer, nullable=False)  # 0-21
    stress_level = db.Column(db.Integer, nullable=False)  # 0-10 stress level
    
    # Risk level
    risk_level = db.Column(db.String(20), nullable=False)  # Low, Moderate, High
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional notes/insights
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            'assessment_id': self.assessment_id,
            'user_id': self.user_id,
            'phq9_score': self.phq9_score,
            'gad7_score': self.gad7_score,
            'stress_score': self.stress_score,
            'risk_level': self.risk_level,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<Assessment {self.assessment_id} - Risk: {self.risk_level}>'


class Conversation(db.Model):
    """Conversation model for AI chat messages"""
    
    __tablename__ = 'conversations'
    
    conversation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Message details
    message_text = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    sentiment_score = db.Column(db.Float, nullable=True)  # -1 to +1 (VADER)
    
    # Session grouping
    session_id = db.Column(db.String(36), nullable=False, index=True)  # UUID
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    crisis_logs = db.relationship('CrisisLog', backref='conversation', lazy='dynamic')
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'message_text': self.message_text,
            'sender': self.sender,
            'sentiment_score': self.sentiment_score,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Conversation {self.conversation_id} - {self.sender}>'


class CrisisLog(db.Model):
    """Crisis log model for tracking detected crises"""
    
    __tablename__ = 'crisis_logs'
    
    crisis_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=True)
    
    # Crisis details
    crisis_score = db.Column(db.Integer, nullable=False)  # 0-5
    keywords_matched = db.Column(db.ARRAY(db.String), nullable=True)  # PostgreSQL array
    sentiment_score = db.Column(db.Float, nullable=True)
    
    # Action taken
    action_taken = db.Column(db.String(50), nullable=False)  # 'alert_sent', 'resources_displayed', 'no_action'
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    guardian_alerts = db.relationship('GuardianAlert', backref='crisis', lazy='dynamic')
    
    def to_dict(self):
        """Convert crisis log to dictionary"""
        return {
            'crisis_id': self.crisis_id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'crisis_score': self.crisis_score,
            'keywords_matched': self.keywords_matched,
            'sentiment_score': self.sentiment_score,
            'action_taken': self.action_taken,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CrisisLog {self.crisis_id} - Score: {self.crisis_score}>'


class GuardianAlert(db.Model):
    """Guardian alert model for WhatsApp notifications"""
    
    __tablename__ = 'guardian_alerts'
    
    alert_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    crisis_id = db.Column(db.Integer, db.ForeignKey('crisis_logs.crisis_id'), nullable=True)
    
    # Guardian details
    guardian_phone = db.Column(db.String(15), nullable=False)
    
    # Alert details
    alert_level = db.Column(db.String(20), nullable=False)  # 'moderate', 'severe', 'crisis'
    message_text = db.Column(db.Text, nullable=False)
    
    # Delivery status
    delivery_status = db.Column(db.String(20), nullable=False, default='pending')  # 'sent', 'delivered', 'failed', 'pending'
    twilio_sid = db.Column(db.String(50), nullable=True)  # Twilio message ID
    
    # Timestamps
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert guardian alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'crisis_id': self.crisis_id,
            'guardian_phone': self.guardian_phone,
            'alert_level': self.alert_level,
            'delivery_status': self.delivery_status,
            'sent_at': self.sent_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }
    
    def __repr__(self):
        return f'<GuardianAlert {self.alert_id} - Level: {self.alert_level}>'


class GameProgress(db.Model):
    """Game progress model for tracking relaxation activities"""
    
    __tablename__ = 'games_progress'
    
    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Game details
    game_name = db.Column(db.String(50), nullable=False)  # 'breathe_balance', 'color_mood', etc.
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convert game progress to dictionary"""
        return {
            'progress_id': self.progress_id,
            'user_id': self.user_id,
            'game_name': self.game_name,
            'completed': self.completed,
            'score': self.score,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<GameProgress {self.progress_id} - {self.game_name}>'
