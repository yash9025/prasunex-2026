"""Application configuration module using Pydantic Settings.

Enforces strict typing, environment variable binding, and secure defaults.
"""

from typing import List, Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for LearningBridge backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core Application Settings
    APP_NAME: str = "LearningBridge"
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/v1"
    SECRET_KEY: str = Field(
        default="learningbridge-insecure-dev-secret-key-change-in-production-2026",
        description="HMAC secret key used for signing JWT tokens.",
    )

    # JWT Authentication Parameters
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "learningbridge-auth"
    JWT_AUDIENCE: str = "learningbridge-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8-hour workday session

    # Database Settings
    DATABASE_URL: str = Field(
        default="sqlite:///./learningbridge.db",
        description="SQLAlchemy database connection URL (PostgreSQL in Docker/production, SQLite for dev/test).",
    )
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis Broker Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Synthetic Safety & Demo Controls
    SYNTHETIC_DATA_FLAG: bool = True
    DEMO_AUTH_ENABLED: bool = True
    MAX_CSV_UPLOAD_SIZE_BYTES: int = 2 * 1024 * 1024  # 2MB
    MAX_CSV_ROWS: int = 5000

    # Grounded AI Drafting Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Optional Google Gemini API key.")
    DRAFTING_MODEL: str = "gemini-2.5-flash"
    DRAFTING_TIMEOUT_SECONDS: int = 10


settings = Settings()
