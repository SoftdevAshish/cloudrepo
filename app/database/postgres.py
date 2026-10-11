"""PostgreSQL connection (SQLAlchemy/SQLModel). Configure with DATABASE_URL or DB_* settings."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.core.database import DEFAULT, get_engine, get_session


def get_postgres_engine(name: str = DEFAULT) -> Engine:
    return get_engine(name)


def postgres_session(name: str = DEFAULT) -> Session:
    return Session(get_engine(name))


def ping_postgres() -> bool:
    with postgres_session() as session:
        session.exec(text("SELECT 1"))
    return True


__all__ = ["get_postgres_engine", "get_session", "ping_postgres", "postgres_session"]
