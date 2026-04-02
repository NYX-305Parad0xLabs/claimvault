from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from app.core.paths import app_data_dir


def default_database_url() -> str:
    storage = app_data_dir("claimvault")
    return f"sqlite:///{storage / 'claimvault.db'}"


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ClaimVault"
    environment: str = "development"
    version: str = "0.1.0"
    database_url: str = Field(default_factory=default_database_url)
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
