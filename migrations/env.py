"""Alembic environment.

Target database, in order of precedence:
  1. a connection passed in by app code (`app.core.migrations.upgrade_database`)
  2. `alembic -x db=<name>`: a named database from settings (`default` or a DATABASES key)
  3. the default database from settings
"""

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel

import app.features.roles.models  # noqa: F401
import app.features.todos.models  # noqa: F401
import app.features.users.models  # noqa: F401
from app.core.config import settings

config = context.config
target_metadata = SQLModel.metadata


def _url() -> str:
    name = context.get_x_argument(as_dictionary=True).get("db", "default")
    if name == "default":
        return settings.default_database_url
    try:
        return settings.databases[name]
    except KeyError:
        raise SystemExit(f"Unknown database '{name}'") from None


def _configure(**kwargs: object) -> None:
    context.configure(target_metadata=target_metadata, compare_type=True, **kwargs)  # type: ignore[arg-type]


def _run(connection: Connection) -> None:
    _configure(connection=connection, render_as_batch=connection.dialect.name == "sqlite")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    _configure(url=_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    engine = create_engine(_url())
    with engine.connect() as conn:
        _run(conn)
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
