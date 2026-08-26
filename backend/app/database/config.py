"""
Application settings loaded from environment / .env file.
Uses pydantic-settings for typed configuration.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "FloodShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/floodshield"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security / JWT
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    # ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
     
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://flood-shield-five.vercel.app"
    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # External services
    RISK_ENGINE_URL: str = "http://localhost:8001"
    ROUTE_ENGINE_URL: str = "http://localhost:8002"
    WEATHER_API_KEY: str = ""
    FLOOD_DATA_API_KEY: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
