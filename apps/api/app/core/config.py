from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./claimvault.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    fastapi_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
