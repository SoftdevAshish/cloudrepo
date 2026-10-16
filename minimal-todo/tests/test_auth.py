"""REQ-AUTH-1..4 (see docs/requirements.md)."""

from app.security import create_access_token

from .conftest import PASSWORD


def test_register_returns_user_without_password(client):
    r = client.post("/api/v1/auth/register", json={"email": "A@Example.com", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@example.com" and body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_email_conflict(client):
    creds = {"email": "a@example.com", "password": PASSWORD}
    client.post("/api/v1/auth/register", json=creds)
    assert client.post("/api/v1/auth/register", json=creds).status_code == 409


def test_weak_password_rejected(client):
    r = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 422


def test_login_success_and_me(client, alice):
    r = client.get("/api/v1/auth/me", headers=alice)
    assert r.status_code == 200 and r.json()["email"] == "alice@example.com"


def test_login_wrong_password_and_unknown_user_look_identical(client, alice):
    bad_pw = client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "wrong-password"}
    )
    unknown = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    assert bad_pw.status_code == unknown.status_code == 401
    assert bad_pw.json() == unknown.json()


def test_missing_or_bad_token_is_401(client):
    assert client.get("/api/v1/todos").status_code == 401
    assert (
        client.get("/api/v1/todos", headers={"Authorization": "Bearer garbage"}).status_code == 401
    )


def test_token_for_deleted_user_is_401(client):
    token = create_access_token(9999)
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )


def test_admin_email_gets_admin_role(client, admin):
    assert client.get("/api/v1/auth/me", headers=admin).json()["role"] == "admin"
