from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app import database, tasks
from app.celery_app import celery_app
from app.main import app
from app.models import Todo, utcnow


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(database, "_engines", {database.DEFAULT: engine})
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
    with database.session_for() as s:
        old = utcnow() - timedelta(days=60)
        s.add(Todo(title="old done", completed=True, updated_at=old))
        s.add(Todo(title="new done", completed=True))
        s.add(Todo(title="old open", completed=False, updated_at=old))
        s.commit()
    assert tasks.purge_completed_todos(30) == 1
    titles = {t["title"] for t in client.get("/todos").json()}
    assert titles == {"new done", "old open"}


def test_runtime_database_selection(client, monkeypatch):
    other = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(other)
    database.register_engine("tenant_b", other)

    client.post("/todos", json={"title": "in default"})
    client.post("/todos", json={"title": "in b"}, headers={"X-Database": "tenant_b"})

    assert [t["title"] for t in client.get("/todos").json()] == ["in default"]
    assert [
        t["title"] for t in client.get("/todos", headers={"X-Database": "tenant_b"}).json()
    ] == ["in b"]
    assert "tenant_b" in client.get("/databases").json()
    assert client.get("/todos", headers={"X-Database": "nope"}).status_code == 400


def test_health_and_ready(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_not_found_paths(client):
    assert client.get("/todos/999").status_code == 404
    assert client.patch("/todos/999", json={"title": "x"}).status_code == 404
    assert client.delete("/todos/999").status_code == 404


def test_pagination(client):
    for i in range(5):
        client.post("/todos", json={"title": f"t{i}"})
    page = client.get("/todos", params={"offset": 1, "limit": 2}).json()
    assert [t["title"] for t in page] == ["t1", "t2"]
    assert client.get("/todos", params={"limit": 0}).status_code == 422


def test_trigger_purge_endpoint(client):
    r = client.post("/tasks/purge-completed", params={"older_than_days": 0})
    assert r.status_code == 202
    assert client.post("/tasks/purge-completed", headers={"X-Database": "nope"}).status_code == 400


def test_notify_task(client):
    todo = client.post("/todos", json={"title": "n"}).json()
    assert tasks.notify_todo_created(todo["id"])["status"] == "notified"
    assert tasks.notify_todo_created(12345)["status"] == "missing"
