# Minimal Todo API

A small FastAPI project that shows the essentials of a well-engineered service:
**authentication**, **policy-based authorization**, **Todo CRUD**, tests, and the **SDLC documents** that connect them.

## Quick start
```bash
cd minimal-todo
pip install -r requirements-dev.txt
cp .env.example .env            # set SECRET_KEY
uvicorn app.main:app --reload   # open http://localhost:8000/docs
pytest -q                       # 24 tests
```

## API
| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | anyone | Create account |
| POST | `/api/v1/auth/login` | anyone | Get access token |
| GET | `/api/v1/auth/me` | signed in | Current user |
| POST | `/api/v1/todos` | user, admin | Create |
| GET | `/api/v1/todos?done=&skip=&limit=` | user (own), admin (all) | List |
| GET | `/api/v1/todos/{id}` | owner, admin | Read |
| PATCH | `/api/v1/todos/{id}` | owner, admin | Partial update |
| DELETE | `/api/v1/todos/{id}` | owner, admin | Delete |
| GET | `/health` | anyone | Liveness |

### Try it
```bash
curl -X POST localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \
     -d '{"email":"me@example.com","password":"correct-horse-battery"}'
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
     -d '{"email":"me@example.com","password":"correct-horse-battery"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST localhost:8000/api/v1/todos -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' -d '{"title":"Learn FastAPI"}'
curl localhost:8000/api/v1/todos -H "Authorization: Bearer $TOKEN"
```
In Swagger UI (`/docs`) there is no login form; paste the token into the request header manually or use curl as above.

## How authorization works
`app/policies.py` holds a table: `user` may CRUD **own** todos, `admin` may do **anything**. No matching policy means denied.
Routes call `authorize(user, action, todo)` for one item and `scope(user, action, select(Todo))` for lists.
Make someone an admin by listing their email in `ADMIN_EMAILS` before they register.

## Project layout
```
minimal-todo/
  app/        main, config, db, models, schemas, security, policies, deps, routers/{auth,todos}
  tests/      unit (policies) + API tests (auth, todos)
  docs/       requirements, design, testing, operations, adr/
  Makefile  pyproject.toml  requirements*.txt  .env.example
```

## SDLC map
| Phase | Artifact |
|---|---|
| 1. Requirements | `docs/requirements.md` (IDs, acceptance criteria, traceability matrix) |
| 2. Design | `docs/design.md`, `docs/adr/` (decisions and their trade-offs) |
| 3. Implementation | `app/` (small layers, typed, linted with ruff) |
| 4. Testing | `docs/testing.md`, `tests/` (every requirement ID covered, negative security tests) |
| 5. Deployment | `docs/operations.md`, CI workflow `.github/workflows/minimal-todo.yml` |
| 6. Maintenance | Dependency updates, ADRs for changed decisions, policy edits with tests |

## Roadmap
Alembic migrations, refresh tokens, rate limiting on login, password reset, return 404 instead of 403 to hide other users' todo ids, Docker image.
