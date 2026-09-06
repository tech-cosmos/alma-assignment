"""Application settings, read from environment variables (see docs/PLAN.md section 6)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EmailProvider = Literal["console", "smtp", "ses"]
StorageProvider = Literal["local", "s3"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://alma:alma@db:5432/alma"
    jwt_secret: str = "change-me"
    jwt_expires_minutes: int = 12 * 60

    attorney_email: str = "attorney@example.com"
    seed_user_email: str = "attorney@example.com"
    seed_user_password: str = "password123"

    email_provider: EmailProvider = "smtp"
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    email_from: str = "no-reply@example.com"

    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    storage_provider: StorageProvider = "local"
    storage_local_dir: str = "/data/resumes"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""

    public_web_url: str = "http://localhost:3000"

    max_resume_bytes: int = Field(default=5 * 1024 * 1024, description="5 MB")
    resume_url_ttl_seconds: int = 300

    @property
    def cookie_secure(self) -> bool:
        return self.public_web_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
