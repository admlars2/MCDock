"""
Application configuration via environment variables.
"""
from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # Root directory containing all Minecraft instance folders
    MC_ROOT: Path = Field(validation_alias="MC_ROOT")

    # CORS origins for the frontend (e.g., ["http://localhost:3000"])
    CORS_ORIGINS: list[AnyHttpUrl] = Field(default=["http://localhost:8080"], validation_alias="CORS_ORIGINS")

    # User
    USER: str = Field(validation_alias="PANEL_USER")
    PASSWORD_HASH: str = Field(validation_alias="PANEL_PASSWORD_HASH")
    JWT_SECRET: str = Field(validation_alias="JWT_SECRET")
    HASH_ALGO: str = "HS256"
    JWT_TTL: timedelta = timedelta(hours=8)

    # Backup configuration
    BACKUP_RETENTION: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=""
    )

settings = Settings()