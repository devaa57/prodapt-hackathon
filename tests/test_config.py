import os
from app.core.config import Settings

def test_settings_load():
    """Verify that settings can be instantiated and load defaults correctly."""
    settings = Settings()
    
    assert settings.app_name == "AI Resume Screening Assistant"
    assert settings.demo_username == "admin"
    assert settings.demo_password == "admin"
    assert settings.jwt_secret_key == "supersecret"
    
def test_settings_env_override():
    """Verify that env vars override settings."""
    os.environ["APP_NAME"] = "Custom Test Name"
    os.environ["DEMO_USERNAME"] = "testuser"
    
    settings = Settings()
    assert settings.app_name == "Custom Test Name"
    assert settings.demo_username == "testuser"
    
    # Clean up
    del os.environ["APP_NAME"]
    del os.environ["DEMO_USERNAME"]
