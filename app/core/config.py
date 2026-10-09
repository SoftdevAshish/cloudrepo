from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

DEV_JWT_SECRET = "dev-insecure-secret-do-not-use-in-production"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"  # set to "production" in deployments

    # Database. Option 1: a full URL.
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

    # Run `alembic upgrade head` automatically when a database is first used. Convenient for
    # development and for named databases created on the fly; disable in production and run
    # `python -m scripts.migrate` as a deploy step instead (see docs/04-deployment.md).
    auto_migrate: bool = True

    # Authentication
    jwt_secret_key: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    # Optional first administrator, created on startup when both are set.
    admin_email: str | None = None
    admin_password: str | None = None

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> "Settings":
        if self.environment == "production" and (
            self.jwt_secret_key == DEV_JWT_SECRET
            or self.jwt_secret_key.startswith("change-me")
            or len(self.jwt_secret_key) < 32
        ):
            raise ValueError("JWT_SECRET_KEY must be a real secret of >= 32 chars in production")
        return self

    @property
    def default_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_driver.startswith("sqlite"):
            return URL.create("sqlite", database=self.db_name).render_as_string()
        return URL.create(
            self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()
