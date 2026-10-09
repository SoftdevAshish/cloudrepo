import time
from datetime import timedelta

import jwt

from app.core.config import settings
from app.core.security import ACCESS, create_token
from tests.conftest import PASSWORD, auth, login, register


def test_register_login_me(client):
    user = register(client, "Alice@Example.com")
    assert user["email"] == "alice@example.com"
    assert user["role"] == "user"
    assert "password" not in user
    assert "hashed_password" not in user
    tokens = login(client, "alice@example.com")
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.json()["email"] == "alice@example.com"


def test_register_validation_and_duplicates(client):
    register(client, "a@example.com")
    dup = client.post("/auth/register", json={"email": "a@example.com", "password": PASSWORD})
    assert dup.status_code == 409
    weak = client.post("/auth/register", json={"email": "b@example.com", "password": "short"})
    assert weak.status_code == 422
    bad = client.post("/auth/register", json={"email": "nope", "password": PASSWORD})
    assert bad.status_code == 422


def test_login_failures_are_indistinguishable(client):
    register(client, "a@example.com")
    wrong = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-pass-1"})
    unknown = client.post(
        "/auth/login", json={"email": "x@example.com", "password": "wrong-pass-1"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_protected_routes_require_token(client):
    assert client.get("/todos").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_refresh_flow_and_token_types(client):
    register(client, "a@example.com")
    tokens = login(client, "a@example.com")
    new = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert new.status_code == 200
    # an access token is not a refresh token, and vice versa
    assert (
        client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code
        == 401
    )
    as_access = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert client.get("/auth/me", headers=as_access).status_code == 401


def test_expired_and_forged_tokens_rejected(client):
    register(client, "a@example.com")
    expired = create_token(1, "default", ACCESS, timedelta(seconds=-1))
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    forged = jwt.encode(
        {"sub": "1", "type": ACCESS, "db": "default", "exp": time.time() + 60},
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_deactivated_user_loses_access(client):
    admin = auth(client, "admin@example.com", admin=True)
    headers = auth(client, "a@example.com")
    uid = client.get("/auth/me", headers=headers).json()["id"]
    client.patch(f"/users/{uid}", json={"is_active": False}, headers=admin)
    assert client.get("/auth/me", headers=headers).status_code == 401
    r = client.post("/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert r.status_code == 401
