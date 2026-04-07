"""
Application configuration using TOML + Environment Variables (Industry Standard)

Configuration Hierarchy (highest priority first):
1. Environment Variables (.env file or system env)
2. TOML Configuration (config.toml)
3. Default Values (hardcoded fallbacks)

This approach follows industry best practices:
- TOML for structured, non-sensitive config (committed to git)
- .env for secrets only (gitignored)
- Environment variables for production overrides
"""
import sys
import os
from pathlib import Path
from typing import List, Optional

# Python 3.11+ has tomllib built-in, older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python <3.11. Install with: pip install tomli"
        )

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Load .env files first (for secrets).
# Support both project-root .env and backend/.env depending on run directory.
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[3]
_BACKEND_ROOT = _THIS_FILE.parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_BACKEND_ROOT / ".env")


def load_toml_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from TOML file"""
    if config_path is None:
        # Look for config.toml in project root
        # In Docker: /app/config.toml
        # In local dev: 3 levels up from this file
        docker_path = Path("/app/config.toml")
        if docker_path.exists():
            config_path = docker_path
        else:
            # Local development path (3 levels up from this file)
            config_path = Path(__file__).parent.parent.parent.parent / "config.toml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Please create config.toml in the project root directory."
        )
    
    with open(config_path, "rb") as f:
        return tomllib.load(f)


# Load TOML configuration
_toml_config = load_toml_config()


class Settings(BaseSettings):
    """
    Application settings with TOML + Environment Variable support
    
    Priority Order:
    1. Environment Variables (highest)
    2. TOML config.toml
    3. Default values (lowest)
    """
    
    # Application
    APP_NAME: str = Field(default=_toml_config["app"]["name"])
    APP_VERSION: str = Field(default=_toml_config["app"]["version"])
    DEBUG: bool = Field(default=_toml_config["app"]["debug"], env="DEBUG")
    
    # API
    API_PREFIX: str = Field(default=_toml_config["api"]["prefix"])
    API_HOST: str = Field(default=_toml_config["api"]["host"], env="API_HOST")
    API_PORT: int = Field(default=_toml_config["api"]["port"], env="API_PORT")
    
    # Security (Override with environment variables in production)
    SECRET_KEY: str = Field(default=_toml_config["security"]["secret_key"], env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default=_toml_config["security"]["jwt_secret_key"], env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default=_toml_config["security"]["jwt_algorithm"])
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=_toml_config["security"]["access_token_expire_minutes"])
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=_toml_config["security"]["refresh_token_expire_days"])
    
    # Database - PostgreSQL
    DATABASE_URL: str = Field(default=_toml_config["database"]["url"], env="DATABASE_URL")
    
    # Vector Database - Qdrant
    QDRANT_URL: str = Field(default=_toml_config["qdrant"]["url"], env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(default=_toml_config["qdrant"]["api_key"], env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = Field(default=_toml_config["qdrant"]["collection_name"])
    QDRANT_EMBEDDING_DIM: int = Field(default=_toml_config["qdrant"]["embedding_dim"])
    
    # Ollama LLM
    OLLAMA_API_URL: str = Field(default=_toml_config["ollama"]["api_url"], env="OLLAMA_API_URL")
    OLLAMA_MODEL: str = Field(default=_toml_config["ollama"]["model"], env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(default=_toml_config["ollama"]["timeout"], env="OLLAMA_TIMEOUT")
    
    # LSTM Model
    LSTM_MODEL_PATH: str = Field(default=_toml_config["lstm"]["model_path"])
    LSTM_VOCAB_PATH: str = Field(default=_toml_config["lstm"]["vocab_path"])
    LSTM_MAX_LENGTH: int = Field(default=_toml_config["lstm"]["max_length"])
    LSTM_HIDDEN_SIZE: int = Field(default=_toml_config["lstm"]["hidden_size"])
    LSTM_NUM_LAYERS: int = Field(default=_toml_config["lstm"]["num_layers"])
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=_toml_config["cors"]["origins"])
    
    # Twilio WhatsApp (Secrets loaded from .env)
    TWILIO_ACCOUNT_SID: str = Field(default=_toml_config["whatsapp"]["account_sid"], env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default=_toml_config["whatsapp"]["auth_token"], env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM: str = Field(default=_toml_config["whatsapp"]["from_number"], env="TWILIO_WHATSAPP_FROM")
    FAST2SMS_API_KEY: str = Field(default="", env="FAST2SMS_API_KEY")

    # SMTP email alerts
    SMTP_HOST: str = Field(default="", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(default="", env="SMTP_FROM_EMAIL")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Crisis Detection
    CRISIS_DETECTION_THRESHOLD: int = Field(default=_toml_config["crisis_detection"]["threshold"])
    GUARDIAN_ALERT_COOLDOWN_HOURS: int = Field(
        default=_toml_config["crisis_detection"]["guardian_alert_cooldown_hours"],
        env="GUARDIAN_ALERT_COOLDOWN_HOURS",
    )
    
    # Data Retention
    CONVERSATION_RETENTION_DAYS: int = Field(default=_toml_config["data_retention"]["conversation_days"])
    CRISIS_LOG_RETENTION_DAYS: int = Field(default=_toml_config["data_retention"]["crisis_log_days"])
    
    # Logging
    LOG_LEVEL: str = Field(default=_toml_config["logging"]["level"], env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default=_toml_config["logging"]["format"])
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment


# Global settings instance
settings = Settings()


# Convenience function to validate configuration on startup
def validate_config():
    """Validate critical configuration values"""
    errors = []
    
    # Check security keys are not default values in production
    if not settings.DEBUG:
        if "CHANGE-IN-PRODUCTION" in settings.SECRET_KEY:
            errors.append("SECRET_KEY must be changed in production")
        if "CHANGE-IN-PRODUCTION" in settings.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY must be changed in production")
    
    # Check database URL is set
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is not configured")
    
    if errors:
        raise ValueError(
            f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    return True
