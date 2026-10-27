# Simple CRUD

FastAPI + SQLAlchemy 2.0 ORM + PostgreSQL, run with Docker Compose.

```bash
docker compose up --build      # API on http://localhost:8000/docs
```

| Method | Path | Action |
|---|---|---|
| POST | `/items` | create |
| GET | `/items` | list (`skip`, `limit`) |
| GET | `/items/{id}` | read |
| PATCH | `/items/{id}` | partial update |
| DELETE | `/items/{id}` | delete |

```bash
curl -X POST localhost:8000/items -H 'content-type: application/json' \
  -d '{"name":"pen","price":1.5}'
```

Layout: `database.py` (engine/session), `models.py` (ORM), `schemas.py` (Pydantic), `crud.py` (queries), `main.py` (routes). Tables are created on startup; use Alembic if the schema will evolve.

Tests (SQLite, no Postgres needed): `pip install -r requirements.txt pytest httpx && pytest`
