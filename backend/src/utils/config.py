"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "NeurowellCA"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database - PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql://neurowellca_user:neurowellca_password_2026@localhost:5432/neurowellca_db",
        env="DATABASE_URL"
    )
    
    # Vector Database - Qdrant
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(default="", env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = "neurowellca_conversations"
    QDRANT_EMBEDDING_DIM: int = 384  # sentence-transformers/all-MiniLM-L6-v2
    
    # Ollama LLM
    OLLAMA_API_URL: str = Field(default="http://localhost:11434", env="OLLAMA_API_URL")
    OLLAMA_MODEL: str = Field(default="llama3.2:3b", env="OLLAMA_MODEL")
    
    # LSTM Model
    LSTM_MODEL_PATH: str = "src/ml_models/lstm_chat_summarizer.pth"
    LSTM_VOCAB_PATH: str = "src/ml_models/lstm_vocab.json"
    LSTM_MAX_LENGTH: int = 512
    LSTM_HIDDEN_SIZE: int = 256
    LSTM_NUM_LAYERS: int = 2
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000"
    ]
    
    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM: str = Field(default="", env="TWILIO_WHATSAPP_FROM")
    
    # Crisis Detection
    CRISIS_DETECTION_THRESHOLD: int = 2
    GUARDIAN_ALERT_COOLDOWN_HOURS: int = 24
    
    # Data Retention
    CONVERSATION_RETENTION_DAYS: int = 30
    CRISIS_LOG_RETENTION_DAYS: int = 90
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
