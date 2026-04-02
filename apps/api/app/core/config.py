from __future__ import annotations

import secrets

from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from app.core.paths import app_data_dir


def default_database_url() -> str:
    storage = app_data_dir("claimvault")
    return f"sqlite:///{storage / 'claimvault.db'}"


def default_evidence_root() -> Path:
    return app_data_dir("claimvault") / "evidence"


def default_export_root() -> Path:
    return app_data_dir("claimvault") / "exports"


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ClaimVault"
    environment: str = "development"
    version: str = "0.1.0"
    database_url: str = Field(default_factory=default_database_url)
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 60
    token_algorithm: str = "HS256"
    evidence_root: Path = Field(default_factory=default_evidence_root)
    max_evidence_size_bytes: int = 10 * 1024 * 1024
    export_root: Path = Field(default_factory=default_export_root)
    vault_packager: str = "default"
