from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Option 1: a full URL.
    database_url: str | None = None
    # Option 2: individual parts, used when DATABASE_URL is not set.
    db_driver: str = "sqlite"  # sqlite | postgresql+psycopg | mysql+pymysql ...
    db_host: str | None = None
    db_port: int | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_name: str = "todos.db"
    # Extra named connections selectable at runtime, e.g.
    # DATABASES='{"tenant_a": "postgresql+psycopg://u:p@host/a", "tenant_b": "sqlite:///./b.db"}'
    databases: dict[str, str] = {}

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    @property
    def default_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_driver.startswith("sqlite"):
            return f"sqlite:///./{self.db_name}"
        return URL.create(
            self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()
