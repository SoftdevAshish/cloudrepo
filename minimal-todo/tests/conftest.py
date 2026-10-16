import os

os.environ["BCRYPT_ROUNDS"] = "4"  # fast hashing in tests; must be set before app imports
os.environ["ADMIN_EMAILS"] = "admin@example.com"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import create_engine  # noqa: E402

from app import db  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db.set_engine(engine)  # fresh in-memory database per test
    with TestClient(app) as c:  # lifespan runs init_db() against the test engine
        yield c
    db.set_engine(None)
    engine.dispose()


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    """Register + log in; return Authorization headers."""
    creds = {"email": email, "password": PASSWORD}
    assert client.post("/api/v1/auth/register", json=creds).status_code == 201
    token = client.post("/api/v1/auth/login", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice(client):
    return auth_headers(client, "alice@example.com")


@pytest.fixture
def bob(client):
    return auth_headers(client, "bob@example.com")


@pytest.fixture
def admin(client):
    return auth_headers(client, "admin@example.com")
