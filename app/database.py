import threading
from collections.abc import Iterator

from fastapi import Header, HTTPException
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

DEFAULT = "default"

_engines: dict[str, Engine] = {}
_lock = threading.Lock()


def make_engine(url: str) -> Engine:
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)


def known_databases() -> set[str]:
    return {DEFAULT, *settings.databases, *_engines}


def register_engine(name: str, engine: Engine) -> None:
    """Register (or replace) a named engine at runtime."""
    with _lock:
        old = _engines.get(name)
        _engines[name] = engine
    if old is not None and old is not engine:
        old.dispose()


def get_engine(name: str = DEFAULT) -> Engine:
    """Return the engine for `name`, creating it and its tables on first use."""
    engine = _engines.get(name)
    if engine is not None:
        return engine
    with _lock:
        if name in _engines:
            return _engines[name]
        url = settings.default_database_url if name == DEFAULT else settings.databases.get(name)
        if url is None:
            raise KeyError(name)
        engine = make_engine(url)
        SQLModel.metadata.create_all(engine)
        _engines[name] = engine
        return engine


def init_db() -> None:
    get_engine(DEFAULT)


def session_for(name: str = DEFAULT) -> Session:
    return Session(get_engine(name))


def get_session(x_database: str | None = Header(default=None)) -> Iterator[Session]:
    """Pick the database per request via the `X-Database` header (default if absent)."""
    name = x_database or DEFAULT
    try:
        engine = get_engine(name)
    except KeyError:
        raise HTTPException(400, f"Unknown database '{name}'") from None
    with Session(engine) as session:
        yield session
