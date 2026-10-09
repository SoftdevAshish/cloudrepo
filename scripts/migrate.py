"""Apply migrations to the default database and every configured named database.

python -m scripts.migrate            # all databases
python -m scripts.migrate tenant_a   # one database
"""

import sys

from app.core.config import settings
from app.core.database import DEFAULT, make_engine
from app.core.migrations import upgrade_database


def targets(only: list[str]) -> dict[str, str]:
    available = {DEFAULT: settings.default_database_url, **settings.databases}
    unknown = set(only) - set(available)
    if unknown:
        raise SystemExit(f"Unknown database(s): {', '.join(sorted(unknown))}")
    return {k: v for k, v in available.items() if not only or k in only}


def main(argv: list[str]) -> None:
    for name, url in targets(argv).items():
        engine = make_engine(url)
        try:
            upgrade_database(engine)
        finally:
            engine.dispose()
        print(f"migrated {name}")  # noqa: T201


if __name__ == "__main__":
    main(sys.argv[1:])
