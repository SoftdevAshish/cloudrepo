def test_crud_flow(client, alice):
    r = client.post("/todos", json={"title": "write code"}, headers=alice)
    assert r.status_code == 201
    todo = r.json()
    assert todo["completed"] is False

    assert client.get(f"/todos/{todo['id']}", headers=alice).json()["title"] == "write code"

    r = client.patch(f"/todos/{todo['id']}", json={"completed": True}, headers=alice)
    assert r.json()["completed"] is True
    assert r.json()["title"] == "write code"

    assert len(client.get("/todos", params={"completed": True}, headers=alice).json()) == 1
    assert client.get("/todos", params={"completed": False}, headers=alice).json() == []

    assert client.delete(f"/todos/{todo['id']}", headers=alice).status_code == 204
    assert client.get(f"/todos/{todo['id']}", headers=alice).status_code == 404


def test_validation(client, alice):
    assert client.post("/todos", json={"title": ""}, headers=alice).status_code == 422


def test_not_found_paths(client, alice):
    assert client.get("/todos/999", headers=alice).status_code == 404
    assert client.patch("/todos/999", json={"title": "x"}, headers=alice).status_code == 404
    assert client.delete("/todos/999", headers=alice).status_code == 404


def test_pagination(client, alice):
    for i in range(5):
        client.post("/todos", json={"title": f"t{i}"}, headers=alice)
    page = client.get("/todos", params={"offset": 1, "limit": 2}, headers=alice).json()
    assert [t["title"] for t in page] == ["t1", "t2"]
    assert client.get("/todos", params={"limit": 0}, headers=alice).status_code == 422


def test_owner_is_taken_from_token_not_payload(client, alice, bob):
    me = client.get("/auth/me", headers=alice).json()["id"]
    r = client.post("/todos", json={"title": "x", "owner_id": 999}, headers=alice)
    assert r.json()["owner_id"] == me


def test_users_only_see_their_own_todos(client, alice, bob):
    mine = client.post("/todos", json={"title": "alice's"}, headers=alice).json()
    client.post("/todos", json={"title": "bob's"}, headers=bob)
    assert [t["title"] for t in client.get("/todos", headers=alice).json()] == ["alice's"]
    assert [t["title"] for t in client.get("/todos", headers=bob).json()] == ["bob's"]
    # instance-level checks on someone else's todo -> 403
    assert client.get(f"/todos/{mine['id']}", headers=bob).status_code == 403
    assert (
        client.patch(f"/todos/{mine['id']}", json={"title": "pwn"}, headers=bob).status_code == 403
    )
    assert client.delete(f"/todos/{mine['id']}", headers=bob).status_code == 403
    assert client.get(f"/todos/{mine['id']}", headers=alice).json()["title"] == "alice's"


def test_admin_manages_everything(client, alice, admin):
    todo = client.post("/todos", json={"title": "alice's"}, headers=alice).json()
    assert len(client.get("/todos", headers=admin).json()) == 1
    r = client.patch(f"/todos/{todo['id']}", json={"completed": True}, headers=admin)
    assert r.status_code == 200
    assert client.delete(f"/todos/{todo['id']}", headers=admin).status_code == 204
