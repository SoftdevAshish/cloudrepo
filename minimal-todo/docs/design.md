# 2. Design (SDLC phase: Design)

## Architecture
Small layered design. Each layer has one job and depends only on the layer below it.

```
 HTTP client
     |
 app/main.py            FastAPI app, router wiring, /health
     |
 app/routers/           HTTP layer: auth.py, todos.py  (validate input, call policy, talk to DB)
     |        \
     |         app/policies.py   WHO may do WHAT (authorization, pure logic, no HTTP/DB)
     |         app/deps.py       get_current_user (authentication via Bearer token)
     |
 app/security.py        bcrypt hashing + JWT create/decode
 app/models.py          SQLModel tables (User, Todo)
 app/schemas.py         Pydantic request/response models (the API contract)
 app/db.py              engine + per-request session dependency
 app/config.py          settings from environment
```

## Request flow (create a todo)
1. Client sends `POST /api/v1/todos` with `Authorization: Bearer <jwt>`.
2. `get_current_user` verifies the token signature and expiry, loads the user, rejects inactive users (**authentication**, else 401).
3. The route calls `authorize(user, CREATE)` (**authorization**, else 403).
4. Pydantic validated the body (else 422); the route inserts the row with `owner_id = user.id` and commits.
5. The response is shaped by `TodoOut`.

## Data model
```
user:  id PK | email UNIQUE | password_hash | role | is_active | created_at
todo:  id PK | owner_id FK -> user.id (indexed) | title | description | done | created_at | updated_at
```

## Authorization design: policy based
Permissions live in one table in `app/policies.py`:

| Role | Actions | Resource | Condition |
|---|---|---|---|
| user | create, read, update, delete | todo | `own` (owner_id == user.id) |
| admin | `*` (all) | todo | `any` |

Rules of the engine:
- **Default deny**: no matching policy means not allowed.
- `can(user, action, obj)` answers per instance; `scope(user, action, stmt)` adds the equivalent `WHERE` to list queries so that forbidden rows are never loaded.
- To change permissions you edit data (add a `Policy`), not route code. Adding a role is one line.
- Authentication (who are you) and authorization (what may you do) are separate modules.

## Security design
| Threat | Mitigation |
|---|---|
| Stolen database | bcrypt password hashes with per-password salt |
| Forged token | HS256 signature with a secret from the environment; `exp` and `sub` required |
| Account enumeration | Same 401 message for unknown email and wrong password; a dummy hash check keeps timing similar |
| Accessing someone else's data (IDOR) | Policy check on every instance access; list queries scoped in SQL |
| Mass assignment (e.g. changing `owner_id`) | Update schema has no `owner_id`; unknown fields are ignored |
| SQL injection | ORM with bound parameters only |
| Privilege escalation at registration | Role is never taken from the request; admin only via `ADMIN_EMAILS` |

Known limitation: a user probing todo ids learns whether an id exists (404) or belongs to someone else (403). If that matters, return 404 for both.

## Technology choices
See `docs/adr/0001-policy-table-authorization.md`. FastAPI + SQLModel (SQLAlchemy) + SQLite by default (any SQLAlchemy URL works, e.g. PostgreSQL), PyJWT, bcrypt.

## Database evolution
`create_all` at start-up is fine for a minimal app. Before real use, adopt Alembic migrations so schema changes are versioned and reviewed.
