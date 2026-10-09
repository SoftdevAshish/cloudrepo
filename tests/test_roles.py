import pytest

from app.core import database
from app.modules.roles.seed import seed_defaults
from tests.conftest import auth, new_engine


def _role_id(client, admin, name):
    roles = client.get("/roles", headers=admin).json()
    return next(r["id"] for r in roles if r["name"] == name)


def _uid(client, headers):
    return client.get("/auth/me", headers=headers).json()["id"]


# ---------------------------------------------------------------- seeding & access


def test_default_roles_are_seeded(client, admin):
    names = {r["name"]: r["is_system"] for r in client.get("/roles", headers=admin).json()}
    assert names == {"admin": True, "user": True}
    user_rules = client.get(f"/roles/{_role_id(client, admin, 'user')}/policies", headers=admin)
    assert {(p["action"], p["subject"]) for p in user_rules.json()} >= {
        ("manage", "Todo"),
        ("read", "User"),
    }


def test_seeding_is_idempotent_and_keeps_edits(client, admin):
    uid = _role_id(client, admin, "user")
    client.post(f"/roles/{uid}/policies", json={"action": "read", "subject": "Todo"}, headers=admin)
    before = client.get(f"/roles/{uid}/policies", headers=admin).json()
    seed_defaults(database.get_engine())  # e.g. another pod starting
    assert client.get(f"/roles/{uid}/policies", headers=admin).json() == before


def test_role_and_policy_management_is_admin_only(client, alice):
    assert client.get("/roles", headers=alice).status_code == 403
    assert client.post("/roles", json={"name": "x1"}, headers=alice).status_code == 403
    assert client.get("/policies/meta", headers=alice).status_code == 403
    assert client.get("/roles").status_code == 401


def test_policy_meta_lists_valid_options(client, admin):
    meta = client.get("/policies/meta", headers=admin).json()
    assert "manage" in meta["actions"]
    assert "owner_id" in meta["subjects"]["Todo"]
    assert "hashed_password" not in meta["subjects"]["User"]
    assert "${user.id}" in meta["placeholders"]


# ---------------------------------------------------------------- the dynamic part


def test_editing_a_policy_changes_access_immediately(client, alice, bob, admin):
    bobs = client.post("/todos", json={"title": "bob's"}, headers=bob).json()
    assert client.get(f"/todos/{bobs['id']}", headers=alice).status_code == 403

    user_role = _role_id(client, admin, "user")
    added = client.post(
        f"/roles/{user_role}/policies",
        json={"action": "read", "subject": "Todo"},
        headers=admin,
    )
    assert added.status_code == 201

    # same tokens, no redeploy: alice can now read (but not change) everyone's todos
    assert client.get(f"/todos/{bobs['id']}", headers=alice).status_code == 200
    assert len(client.get("/todos", headers=alice).json()) == 1
    assert (
        client.patch(f"/todos/{bobs['id']}", json={"title": "x"}, headers=alice).status_code == 403
    )

    client.delete(f"/policies/{added.json()['id']}", headers=admin)
    assert client.get(f"/todos/{bobs['id']}", headers=alice).status_code == 403


def test_new_role_assigned_to_user(client, alice, bob, admin):
    client.post("/todos", json={"title": "bob's"}, headers=bob)
    r = client.post("/roles", json={"name": "auditor", "description": "read-only"}, headers=admin)
    assert r.status_code == 201
    rid = r.json()["id"]
    client.post(f"/roles/{rid}/policies", json={"action": "read", "subject": "Todo"}, headers=admin)
    client.post(
        f"/roles/{rid}/policies",
        json={"action": "read", "subject": "User", "conditions": {"id": "${user.id}"}},
        headers=admin,
    )

    assert client.get("/todos", headers=alice).json() == []
    patch = client.patch(f"/users/{_uid(client, alice)}", json={"role": "auditor"}, headers=admin)
    assert patch.json()["role"] == "auditor"

    assert len(client.get("/todos", headers=alice).json()) == 1  # sees bob's now
    assert client.post("/todos", json={"title": "no"}, headers=alice).status_code == 403
    mine = client.get("/auth/me/abilities", headers=alice).json()
    assert {
        "action": "read",
        "subject": "Todo",
        "conditions": None,
        "fields": None,
        "inverted": False,
    } in mine
    # placeholder was resolved to the caller's id
    assert any(r["conditions"] == {"id": _uid(client, alice)} for r in mine)


def test_cannot_rule_overrides_earlier_can(client, alice, admin):
    mine = client.post("/todos", json={"title": "keep"}, headers=alice).json()
    user_role = _role_id(client, admin, "user")
    client.post(
        f"/roles/{user_role}/policies",
        json={
            "action": "delete",
            "subject": "Todo",
            "conditions": {"completed": True},
            "inverted": True,
        },
        headers=admin,
    )
    assert client.delete(f"/todos/{mine['id']}", headers=alice).status_code == 204  # not completed
    done = client.post("/todos", json={"title": "d", "completed": True}, headers=alice).json()
    assert client.delete(f"/todos/{done['id']}", headers=alice).status_code == 403


def test_replace_policies_is_atomic(client, admin):
    rid = client.post("/roles", json={"name": "temp"}, headers=admin).json()["id"]
    ok = client.put(
        f"/roles/{rid}/policies",
        json=[{"action": "read", "subject": "Todo"}, {"action": "read", "subject": "User"}],
        headers=admin,
    )
    assert len(ok.json()) == 2
    bad = client.put(
        f"/roles/{rid}/policies",
        json=[{"action": "read", "subject": "Todo"}, {"action": "read", "subject": "Nope"}],
        headers=admin,
    )
    assert bad.status_code == 422
    assert len(client.get(f"/roles/{rid}/policies", headers=admin).json()) == 2  # untouched


def test_update_policy(client, admin):
    rid = client.post("/roles", json={"name": "temp"}, headers=admin).json()["id"]
    pid = client.post(
        f"/roles/{rid}/policies", json={"action": "read", "subject": "Todo"}, headers=admin
    ).json()["id"]
    r = client.put(f"/policies/{pid}", json={"action": "update", "subject": "Todo"}, headers=admin)
    assert r.json()["action"] == "update"
    assert (
        client.put(
            "/policies/9999", json={"action": "read", "subject": "Todo"}, headers=admin
        ).status_code
        == 404
    )


# ---------------------------------------------------------------- validation / safety


@pytest.mark.parametrize(
    "rule",
    [
        {"action": "fly", "subject": "Todo"},  # unknown action
        {"action": "read", "subject": "Secrets"},  # unknown subject
        {"action": "read", "subject": "Todo", "conditions": {"metadata": 1}},  # not a column
        {"action": "read", "subject": "Todo", "conditions": {"__class__": 1}},
        {"action": "read", "subject": "User", "conditions": {"hashed_password": "x"}},  # sensitive
        {"action": "read", "subject": "User", "fields": ["hashed_password"]},
        {"action": "read", "subject": "Todo", "conditions": {"id": {"$where": "1=1"}}},  # operator
        {"action": "read", "subject": "Todo", "conditions": {"id": {"$in": 5}}},  # not a list
        {"action": "read", "subject": "Todo", "conditions": {"owner_id": "${user.password}"}},
        {"action": "read", "subject": "Todo", "conditions": {"owner_id": "${__import__}"}},
        {"action": "read", "subject": "Todo", "conditions": {"id": {"nested": {"a": 1}}}},
        {"action": "read", "subject": "Todo", "conditions": {}},
        {"action": "read", "subject": "all", "conditions": {"id": 1}},
        {"action": "read", "subject": "System", "fields": ["x"]},
        {"action": "read", "subject": "Todo", "fields": []},
        {"action": "read", "subject": "Todo", "fields": ["nope"]},
    ],
)
def test_invalid_policies_are_rejected(client, admin, rule):
    rid = client.post("/roles", json={"name": "temp"}, headers=admin).json()["id"]
    r = client.post(f"/roles/{rid}/policies", json=rule, headers=admin)
    assert r.status_code == 422, r.text


def test_condition_values_are_bound_not_interpolated_into_sql(client, alice, admin):
    rid = client.post("/roles", json={"name": "evil"}, headers=admin).json()["id"]
    client.post(
        f"/roles/{rid}/policies",
        json={"action": "read", "subject": "Todo", "conditions": {"title": "x' OR '1'='1"}},
        headers=admin,
    )
    client.post("/todos", json={"title": "secret"}, headers=alice)
    client.patch(f"/users/{_uid(client, alice)}", json={"role": "evil"}, headers=admin)
    assert client.get("/todos", headers=alice).json() == []


def test_role_name_validation(client, admin):
    for name in ["Admin", "1abc", "a", "has space", "x" * 40, ""]:
        assert client.post("/roles", json={"name": name}, headers=admin).status_code == 422
    assert client.post("/roles", json={"name": "admin"}, headers=admin).status_code == 409


def test_assigning_unknown_role_is_rejected(client, alice, admin):
    r = client.patch(f"/users/{_uid(client, alice)}", json={"role": "ghost"}, headers=admin)
    assert r.status_code == 422


# ---------------------------------------------------------------- guard rails


def test_admin_role_is_protected(client, admin):
    rid = _role_id(client, admin, "admin")
    assert (
        client.post(
            f"/roles/{rid}/policies", json={"action": "read", "subject": "Todo"}, headers=admin
        ).status_code
        == 409
    )
    assert client.put(f"/roles/{rid}/policies", json=[], headers=admin).status_code == 409
    pid = client.get(f"/roles/{rid}/policies", headers=admin).json()[0]["id"]
    assert client.delete(f"/policies/{pid}", headers=admin).status_code == 409
    assert client.delete(f"/roles/{rid}", headers=admin).status_code == 409


def test_system_and_in_use_roles_cannot_be_deleted(client, alice, admin):
    assert (
        client.delete(f"/roles/{_role_id(client, admin, 'user')}", headers=admin).status_code == 409
    )
    rid = client.post("/roles", json={"name": "temp"}, headers=admin).json()["id"]
    client.patch(f"/users/{_uid(client, alice)}", json={"role": "temp"}, headers=admin)
    assert client.delete(f"/roles/{rid}", headers=admin).status_code == 409  # still assigned
    client.patch(f"/users/{_uid(client, alice)}", json={"role": "user"}, headers=admin)
    assert client.delete(f"/roles/{rid}", headers=admin).status_code == 204


def test_role_admin_can_be_delegated_with_policies_only(client, alice, admin):
    """A custom 'role-manager' may manage roles/policies; nothing else is implied."""
    rid = client.post("/roles", json={"name": "role-manager"}, headers=admin).json()["id"]
    for subject in ("Role", "Policy"):
        client.post(
            f"/roles/{rid}/policies", json={"action": "manage", "subject": subject}, headers=admin
        )
    client.patch(f"/users/{_uid(client, alice)}", json={"role": "role-manager"}, headers=admin)
    assert client.get("/roles", headers=alice).status_code == 200
    assert client.get("/databases", headers=alice).status_code == 403
    # still cannot touch the protected admin role
    admin_rid = _role_id(client, alice, "admin")
    assert client.delete(f"/roles/{admin_rid}", headers=alice).status_code == 409


def test_invalid_stored_policy_is_skipped_not_fatal(client, alice, admin):
    """Rows edited directly in the DB must never take the API down."""
    from sqlmodel import select

    from app.modules.roles.models import Policy

    with database.session_for() as s:
        rule = s.exec(select(Policy).where(Policy.subject == "Todo")).first()
        s.add(
            Policy(
                role_id=rule.role_id, action="read", subject="Todo", conditions={"not_a_column": 1}
            )
        )
        s.commit()
    assert client.get("/todos", headers=alice).status_code == 200


def test_roles_are_per_database(client, admin):
    database.register_engine("tenant_b", new_engine())
    b_admin = auth(client, "root@b.example.com", db="tenant_b", admin=True)
    client.post("/roles", json={"name": "only-in-b"}, headers=b_admin)
    assert "only-in-b" in {r["name"] for r in client.get("/roles", headers=b_admin).json()}
    assert "only-in-b" not in {r["name"] for r in client.get("/roles", headers=admin).json()}
