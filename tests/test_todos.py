import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import database, tasks
from app.celery_app import celery_app
from app.main import app
from app.models import Todo, utcnow
from datetime import timedelta


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[database.get_session] = override
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = False
    celery_app.conf.result_backend = "cache+memory://"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_crud_flow(client):
    r = client.post("/todos", json={"title": "write code"})
    assert r.status_code == 201
    todo = r.json()
    assert todo["completed"] is False

    assert client.get(f"/todos/{todo['id']}").json()["title"] == "write code"

    r = client.patch(f"/todos/{todo['id']}", json={"completed": True})
    assert r.json()["completed"] is True
    assert r.json()["title"] == "write code"

    assert len(client.get("/todos", params={"completed": True}).json()) == 1
    assert client.get("/todos", params={"completed": False}).json() == []

    assert client.delete(f"/todos/{todo['id']}").status_code == 204
    assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_validation(client):
    assert client.post("/todos", json={"title": ""}).status_code == 422


def test_purge_task(client):
    with Session(database.engine) as s:
        old = utcnow() - timedelta(days=60)
        s.add(Todo(title="old done", completed=True, updated_at=old))
        s.add(Todo(title="new done", completed=True))
        s.add(Todo(title="old open", completed=False, updated_at=old))
        s.commit()
    assert tasks.purge_completed_todos(30) == 1
    titles = {t["title"] for t in client.get("/todos").json()}
    assert titles == {"new done", "old open"}
