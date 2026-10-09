def _id(client, headers):
    return client.get("/auth/me", headers=headers).json()["id"]


def test_user_lists_only_self_admin_lists_all(client, alice, bob, admin):
    assert [u["email"] for u in client.get("/users", headers=alice).json()] == ["alice@example.com"]
    assert len(client.get("/users", headers=admin).json()) == 3


def test_user_can_read_and_update_self_but_not_others(client, alice, bob):
    me, other = _id(client, alice), _id(client, bob)
    assert client.get(f"/users/{me}", headers=alice).status_code == 200
    assert client.get(f"/users/{other}", headers=alice).status_code == 403
    assert (
        client.patch(f"/users/{other}", json={"email": "x@example.com"}, headers=alice).status_code
        == 403
    )
    r = client.patch(f"/users/{me}", json={"email": "new@example.com"}, headers=alice)
    assert r.json()["email"] == "new@example.com"


def test_field_level_rule_blocks_privilege_escalation(client, alice):
    me = _id(client, alice)
    r = client.patch(f"/users/{me}", json={"role": "admin"}, headers=alice)
    assert r.status_code == 403
    assert "role" in r.json()["detail"]
    assert client.get("/auth/me", headers=alice).json()["role"] == "user"
    assert client.patch(f"/users/{me}", json={"is_active": False}, headers=alice).status_code == 403


def test_admin_can_change_roles(client, alice, admin):
    me = _id(client, alice)
    r = client.patch(f"/users/{me}", json={"role": "admin"}, headers=admin)
    assert r.json()["role"] == "admin"


def test_email_conflict(client, alice, bob):
    r = client.patch(
        f"/users/{_id(client, alice)}", json={"email": "bob@example.com"}, headers=alice
    )
    assert r.status_code == 409


def test_password_change(client, alice):
    me = _id(client, alice)
    assert (
        client.patch(
            f"/users/{me}", json={"password": "a-brand-new-pass"}, headers=alice
        ).status_code
        == 200
    )
    ok = client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "a-brand-new-pass"}
    )
    assert ok.status_code == 200


def test_only_admin_deletes_users_and_their_todos_go_too(client, alice, admin):
    me = _id(client, alice)
    client.post("/todos", json={"title": "bye"}, headers=alice)
    assert client.delete(f"/users/{me}", headers=alice).status_code == 403
    assert client.delete(f"/users/{me}", headers=admin).status_code == 204
    assert client.get("/todos", headers=admin).json() == []
    assert client.get(f"/users/{me}", headers=admin).status_code == 404
