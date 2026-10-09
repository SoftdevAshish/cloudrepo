import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlmodel import SQLModel

from app.core.database import make_engine
from app.core.migrations import downgrade_database, upgrade_database

TABLES = {"user", "role", "policy", "todo"}


def _engine(tmp_path, name="m.db"):
    return make_engine(f"sqlite:///{tmp_path / name}")


def test_migrations_produce_exactly_the_model_schema(tmp_path):
    """Fails when someone changes a model without writing a migration."""
    engine = _engine(tmp_path)
    upgrade_database(engine)

    def app_tables_only(obj, name, type_, reflected, compare_to):  # other tests define tables too
        return type_ != "table" or name in TABLES

    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"include_object": app_tables_only})
        diff = compare_metadata(context, SQLModel.metadata)
    assert diff == []


def test_upgrade_is_idempotent(tmp_path):
    engine = _engine(tmp_path)
    upgrade_database(engine)
    upgrade_database(engine)
    assert set(sa.inspect(engine).get_table_names()) >= TABLES


def test_downgrade_removes_tables(tmp_path):
    engine = _engine(tmp_path)
    upgrade_database(engine)
    downgrade_database(engine, "base")
    assert not (TABLES & set(sa.inspect(engine).get_table_names()))


def test_adopts_database_created_before_alembic(tmp_path):
    """Releases <= 0.4 used create_all; upgrading must not fail on their tables."""
    engine = _engine(tmp_path)
    SQLModel.metadata.create_all(engine)
    upgrade_database(engine)
    assert "alembic_version" in sa.inspect(engine).get_table_names()


def test_adds_missing_tables_to_a_0_3_database(tmp_path):
    engine = _engine(tmp_path)
    SQLModel.metadata.create_all(
        engine, tables=[SQLModel.metadata.tables["user"], SQLModel.metadata.tables["todo"]]
    )
    upgrade_database(engine)
    assert set(sa.inspect(engine).get_table_names()) >= TABLES
