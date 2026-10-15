from app.core.config import settings


def test_settings_loaded():
    """Verify that settings are loaded properly from environment."""
    assert settings.PROJECT_NAME == "AgriDrone AutoMap"
    assert settings.API_V1_STR == "/api/v1"
    assert "postgresql" in settings.DATABASE_URL
    assert "localhost" in settings.REDIS_URL
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:3005" in settings.CORS_ORIGINS
