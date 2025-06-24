"""
Application configuration via environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl


class Settings(BaseSettings):
    # Root directory containing all Minecraft instance folders
    MC_ROOT: str = Field(validation_alias="MC_ROOT")

    # RCON connection settings
    RCON_HOST: str = "127.0.0.1"
    RCON_PORT: int = 25575
    RCON_PASSWORD: str | None = Field(default=None, validation_alias="RCON_PASSWORD")

    # CORS origins for the frontend (e.g., ["http://localhost:3000"])
    CORS_ORIGINS: list[AnyHttpUrl] = Field(default=["*"], validation_alias="CORS_ORIGINS")
    CONTROL_PANEL_BEARER_TOKEN: str = Field(validation_alias="CONTROL_PANEL_BEARER_TOKEN")

    # Backup configuration
    BACKUP_INTERVAL_MINUTES: int = 30
    BACKUP_RETENTION: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=""
    )


settings = Settings()