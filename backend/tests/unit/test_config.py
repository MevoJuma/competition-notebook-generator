from pathlib import Path
from app.core.config import Settings


def test_settings_default_values():
    """Verify settings defaults are populated correctly."""
    settings = Settings()
    assert settings.PROJECT_NAME == "AI Competition Analysis & Notebook Generation Platform"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_ZIP_COMPRESSION_RATIO == 10
    assert isinstance(settings.upload_path, Path)
    assert isinstance(settings.generated_path, Path)


def test_cors_origins_parsing():
    """Verify CORS origins can parse comma-separated strings or list of strings."""
    settings_str = Settings(CORS_ORIGINS="http://localhost:3000, http://test.com")
    assert "http://localhost:3000" in settings_str.CORS_ORIGINS
    assert "http://test.com" in settings_str.CORS_ORIGINS

    settings_list = Settings(CORS_ORIGINS=["http://localhost:3000", "http://test.com"])
    assert len(settings_list.CORS_ORIGINS) == 2
