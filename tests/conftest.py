import os

os.environ.setdefault("BCRYPT_ROUNDS", "4")  # fast hashing in tests; must precede app imports

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine, select  # noqa: E402

from app.celery_app import celery_app  # noqa: E402
from app.core import database  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.users.models import Role, User  # noqa: E402

PASSWORD = "correct-horse-battery"  # noqa: S105


def new_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(database, "_engines", {database.DEFAULT: new_engine()})
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = False
    celery_app.conf.result_backend = "cache+memory://"
    with TestClient(app) as c:
        yield c


def register(client, email, db=None):
    headers = {"X-Database": db} if db else {}
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def login(client, email, db=None):
    headers = {"X-Database": db} if db else {}
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def auth(client, email, db=None, admin=False):
    """Register + login; returns request headers. `admin=True` promotes the user in the DB."""
    register(client, email, db)
    if admin:
        with database.session_for(db or database.DEFAULT) as s:
            user = s.exec(select(User).where(User.email == email)).one()
            user.role = Role.ADMIN
            s.add(user)
            s.commit()
    headers = {"Authorization": f"Bearer {login(client, email, db)['access_token']}"}
    if db:
        headers["X-Database"] = db
    return headers


@pytest.fixture
def alice(client):
    return auth(client, "alice@example.com")


@pytest.fixture
def bob(client):
    return auth(client, "bob@example.com")


@pytest.fixture
def admin(client):
    return auth(client, "admin@example.com", admin=True)


@pytest.fixture
def db_session(client):
    with Session(database.get_engine()) as s:
        yield s
