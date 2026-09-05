from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Screening Assistant"
    debug: bool = False

    # Gemini
    gemini_api_key: str = ""

    # Database
    database_url: Optional[str] = None
    default_org_id: str = "a0000000-0000-0000-0000-000000000001"

    # JWT
    jwt_secret_key: str = "supersecret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Demo Credentials
    demo_username: str = "admin"
    demo_password: str = "admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
