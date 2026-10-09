import pytest
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET, Settings


def test_sqlite_default():
    s = Settings(_env_file=None, database_url=None, db_driver="sqlite", db_name="x.db")
    assert s.default_database_url == "sqlite:///x.db"


def test_sqlite_absolute_path():
    s = Settings(_env_file=None, database_url=None, db_driver="sqlite", db_name="/var/data/x.db")
    assert s.default_database_url == "sqlite:////var/data/x.db"


def test_url_wins_over_parts():
    s = Settings(_env_file=None, database_url="sqlite:///./a.db", db_driver="postgresql+psycopg")
    assert s.default_database_url == "sqlite:///./a.db"


def test_url_built_from_parts_escapes_password():
    s = Settings(
        _env_file=None,
        database_url=None,
        db_driver="postgresql+psycopg",
        db_host="h",
        db_port=5432,
        db_user="u",
        db_password="p@ss/w:rd",
        db_name="d",
    )
    assert s.default_database_url == "postgresql+psycopg://u:p%40ss%2Fw%3Ard@h:5432/d"


@pytest.mark.parametrize("secret", [DEV_JWT_SECRET, "change-me-" + "x" * 40, "short"])
def test_production_rejects_weak_jwt_secret(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", jwt_secret_key=secret)


def test_production_accepts_strong_secret():
    Settings(_env_file=None, environment="production", jwt_secret_key="s" * 40)
