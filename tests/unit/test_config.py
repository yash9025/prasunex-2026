"""Unit tests for configuration validation."""

from app.core.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.APP_NAME == "LearningBridge"
    assert s.SYNTHETIC_DATA_FLAG is True
    assert s.JWT_ALGORITHM == "HS256"
    assert s.JWT_ISSUER == "learningbridge-auth"
    assert s.JWT_AUDIENCE == "learningbridge-api"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert len(s.CORS_ORIGINS) >= 2
