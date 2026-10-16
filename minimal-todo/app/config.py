from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./todo.db"
    secret_key: str = Field(default="dev-only-insecure-secret-change-me-please!", min_length=32)
    access_token_minutes: int = 30
    admin_emails: str = ""
    bcrypt_rounds: int = 12

    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
