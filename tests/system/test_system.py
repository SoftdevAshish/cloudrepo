from datetime import timedelta

from app.core import database
from app.features.todos import tasks
from app.features.todos.models import Todo, utcnow
from tests.conftest import auth, new_engine


def test_health_and_ready_are_public(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_ops_endpoints_are_admin_only(client, alice, admin):
    assert client.get("/api/v1/databases", headers=alice).status_code == 403
    assert client.post("/api/v1/tasks/purge-completed", headers=alice).status_code == 403
    assert client.get("/api/v1/databases").status_code == 401
    assert "default" in client.get("/api/v1/databases", headers=admin).json()
    r = client.post("/api/v1/tasks/purge-completed", params={"older_than_days": 0}, headers=admin)
    assert r.status_code == 202


def test_purge_task(client, alice):
    me = client.get("/api/v1/auth/me", headers=alice).json()["id"]
    with database.session_for() as s:
        old = utcnow() - timedelta(days=60)
        s.add(Todo(title="old done", completed=True, updated_at=old, owner_id=me))
        s.add(Todo(title="new done", completed=True, owner_id=me))
        s.add(Todo(title="old open", completed=False, updated_at=old, owner_id=me))
        s.commit()
    assert tasks.purge_completed_todos(30) == 1
    titles = {t["title"] for t in client.get("/api/v1/todos", headers=alice).json()}
    assert titles == {"new done", "old open"}


def test_notify_task(client, alice):
    todo = client.post("/api/v1/todos", json={"title": "n"}, headers=alice).json()
    assert tasks.notify_todo_created(todo["id"])["status"] == "notified"
    assert tasks.notify_todo_created(12345)["status"] == "missing"


def test_runtime_database_selection(client):
    database.register_engine("tenant_b", new_engine())
    a = auth(client, "alice@example.com")
    b = auth(client, "alice@example.com", db="tenant_b")  # same email, separate user table

    client.post("/api/v1/todos", json={"title": "in default"}, headers=a)
    client.post("/api/v1/todos", json={"title": "in b"}, headers=b)

    assert [t["title"] for t in client.get("/api/v1/todos", headers=a).json()] == ["in default"]
    assert [t["title"] for t in client.get("/api/v1/todos", headers=b).json()] == ["in b"]
    assert client.get("/api/v1/todos", headers={**a, "X-Database": "nope"}).status_code == 400


def test_token_is_bound_to_its_database(client):
    database.register_engine("tenant_b", new_engine())
    a = auth(client, "alice@example.com")
    auth(client, "mallory@example.com", db="tenant_b")
    # a default-DB token must not authenticate against another database
    cross = client.get("/api/v1/auth/me", headers={**a, "X-Database": "tenant_b"})
    assert cross.status_code == 401
