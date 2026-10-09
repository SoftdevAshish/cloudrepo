from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[2]


def _config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    return cfg


def upgrade_database(engine: Engine, revision: str = "head") -> None:
    """Apply migrations to `engine` (any database: default or a named one)."""
    cfg = _config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, revision)


def downgrade_database(engine: Engine, revision: str) -> None:
    cfg = _config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.downgrade(cfg, revision)
