from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    debug: bool

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    demo_username: str
    demo_password: str

    openrouter_api_key: str
    openrouter_model: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()