"""REQ-TODO-1..6 (CRUD) and REQ-AUTHZ-1..4 (policies). See docs/requirements.md."""


def create(client, headers, title="Buy milk", **extra):
    r = client.post("/api/v1/todos", json={"title": title, **extra}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---- CRUD ----------------------------------------------------------------
def test_create_sets_owner_and_defaults(client, alice):
    todo = create(client, alice, description="2 litres")
    assert todo["done"] is False and todo["description"] == "2 litres"
    me = client.get("/api/v1/auth/me", headers=alice).json()
    assert todo["owner_id"] == me["id"]


def test_create_validation(client, alice):
    assert client.post("/api/v1/todos", json={"title": ""}, headers=alice).status_code == 422
    assert client.post("/api/v1/todos", json={}, headers=alice).status_code == 422


def test_read_one_and_404(client, alice):
    todo = create(client, alice)
    assert client.get(f"/api/v1/todos/{todo['id']}", headers=alice).json()["title"] == "Buy milk"
    assert client.get("/api/v1/todos/999", headers=alice).status_code == 404


def test_list_filter_and_pagination(client, alice):
    for i in range(5):
        create(client, alice, title=f"t{i}")
    client.patch("/api/v1/todos/1", json={"done": True}, headers=alice)
    assert len(client.get("/api/v1/todos", headers=alice).json()) == 5
    assert len(client.get("/api/v1/todos?done=true", headers=alice).json()) == 1
    page = client.get("/api/v1/todos?skip=1&limit=2", headers=alice).json()
    assert [t["title"] for t in page] == ["t1", "t2"]
    assert client.get("/api/v1/todos?limit=1000", headers=alice).status_code == 422


def test_partial_update(client, alice):
    todo = create(client, alice, description="keep me")
    r = client.patch(f"/api/v1/todos/{todo['id']}", json={"done": True}, headers=alice)
    assert r.status_code == 200
    body = r.json()
    assert body["done"] is True and body["title"] == "Buy milk" and body["description"] == "keep me"
    assert body["updated_at"] >= todo["updated_at"]


def test_delete(client, alice):
    todo = create(client, alice)
    assert client.delete(f"/api/v1/todos/{todo['id']}", headers=alice).status_code == 204
    assert client.get(f"/api/v1/todos/{todo['id']}", headers=alice).status_code == 404


# ---- Policy-based authorization -------------------------------------------
def test_user_list_only_shows_own_todos(client, alice, bob):
    create(client, alice, title="alice's")
    create(client, bob, title="bob's")
    titles = [t["title"] for t in client.get("/api/v1/todos", headers=alice).json()]
    assert titles == ["alice's"]


def test_user_cannot_read_update_delete_others_todo(client, alice, bob):
    todo = create(client, alice)
    url = f"/api/v1/todos/{todo['id']}"
    assert client.get(url, headers=bob).status_code == 403
    assert client.patch(url, json={"done": True}, headers=bob).status_code == 403
    assert client.delete(url, headers=bob).status_code == 403
    assert client.get(url, headers=alice).json()["done"] is False  # untouched


def test_admin_can_manage_everyones_todos(client, alice, admin):
    todo = create(client, alice)
    url = f"/api/v1/todos/{todo['id']}"
    assert client.get(url, headers=admin).status_code == 200
    assert client.patch(url, json={"title": "edited"}, headers=admin).json()["title"] == "edited"
    assert len(client.get("/api/v1/todos", headers=admin).json()) == 1
    assert client.delete(url, headers=admin).status_code == 204


def test_owner_cannot_be_changed_via_update(client, alice, bob):
    todo = create(client, alice)
    client.patch(f"/api/v1/todos/{todo['id']}", json={"owner_id": 999}, headers=alice)
    assert (
        client.get(f"/api/v1/todos/{todo['id']}", headers=alice).json()["owner_id"]
        == todo["owner_id"]
    )


def test_unknown_role_is_denied_by_default(client, alice):
    from sqlmodel import Session

    from app import db
    from app.models import User

    with Session(db.get_engine()) as s:
        u = s.get(User, 1)
        u.role = "ghost"  # no policy matches -> default deny
        s.add(u)
        s.commit()
    assert client.post("/api/v1/todos", json={"title": "x"}, headers=alice).status_code == 403
    assert client.get("/api/v1/todos", headers=alice).json() == []
