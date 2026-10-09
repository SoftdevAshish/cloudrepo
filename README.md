# Todo API: FastAPI + SQLModel/SQLAlchemy + Celery

## Run
```bash
pip install -r requirements-dev.txt
cp .env.example .env
docker run -p 6379:6379 -d redis            # broker/result backend

uvicorn app.main:app --reload               # API  -> http://localhost:8000/docs
celery -A app.celery_app worker -l info     # worker
celery -A app.celery_app beat -l info       # scheduler (daily purge of old completed todos)
```

## Architecture
NestJS-style modules under `app/modules/<name>/`: `controller.py` (HTTP) -> `service.py` (business rules + authorization) -> `repository.py` (database only), plus `models.py` / `schemas.py`. Cross-cutting code lives in `app/core/` (config, database, security, `casl.py`).

## Authentication & authorization
- JWT bearer auth: `POST /auth/register`, `POST /auth/login` (access + refresh tokens), `POST /auth/refresh`, `GET /auth/me`. Passwords are hashed with bcrypt; tokens are bound to the database they were issued for.
- Authorization uses a CASL-style library (`app/core/casl.py`). **Roles and policies are data in the database**, so they can be changed at runtime through the API with no redeploy. Each user has one role; each role has an ordered list of policies (CASL rules); later policies override earlier ones. The rules are read on every request, so edits apply immediately.
- Two roles are seeded in every database: `admin` (`manage all`, immutable) and `user` (see below; editable). Missing roles are re-created on start, but your edits are never overwritten.

| Role | Todos | Users | Ops (`/databases`, `/tasks/*`) | Roles & policies |
|---|---|---|---|---|
| `user` (default policies) | manage **own** only | read/update **self**; may not change `role` / `is_active` | none | none |
| `admin` | manage all | manage all | allowed | manage all |

- Guards: `get_current_user` (authentication), `check_policies(Action.READ, Todo)` (coarse, class-level), and `ability.authorize(action, instance)` in services (instance and field level, like CASL's `ForbiddenError.throwUnlessCan`). Lists are filtered in SQL with `accessible_by(ability, action, Model)`.

### Managing roles and policies at runtime
A policy is a CASL rule stored as JSON:

| Field | Meaning |
|---|---|
| `action` | `manage` (any), `create`, `read`, `update`, `delete` |
| `subject` | `Todo`, `User`, `Role`, `Policy`, `System` (ops endpoints) or `all` |
| `conditions` | optional row filter, e.g. `{"owner_id": "${user.id}"}`; operators `$eq $ne $in $nin $gt $gte $lt $lte`; placeholders `${user.id}`, `${user.email}`, `${user.role}`, `${user.is_active}` |
| `fields` | optional, restricts the rule to those columns (field-level) |
| `inverted` | `true` makes it a "cannot" rule |

```bash
A="authorization: Bearer $ADMIN_TOKEN"; J='content-type: application/json'
curl :8000/policies/meta -H "$A"                       # valid actions, subjects, fields, placeholders

# 1. create a role
curl -X POST :8000/roles -H "$A" -H "$J" -d '{"name":"auditor","description":"read-only"}'
# 2. give it rules (read every todo, read only yourself in Users)
curl -X POST :8000/roles/3/policies -H "$A" -H "$J" -d '{"action":"read","subject":"Todo"}'
curl -X POST :8000/roles/3/policies -H "$A" -H "$J" \
  -d '{"action":"read","subject":"User","conditions":{"id":"${user.id}"}}'
# 3. assign it
curl -X PATCH :8000/users/5 -H "$A" -H "$J" -d '{"role":"auditor"}'
# change your mind: edit or remove a rule, or replace the whole set atomically
curl -X PUT :8000/policies/7 -H "$A" -H "$J" -d '{"action":"update","subject":"Todo"}'
curl -X DELETE :8000/policies/7 -H "$A"
curl -X PUT :8000/roles/3/policies -H "$A" -H "$J" -d '[{"action":"read","subject":"Todo"}]'
```
Safety: subjects, fields and condition keys are checked against real model columns (no arbitrary attributes, `hashed_password` is off limits), operators are allow-listed, values are bound SQL parameters, the `admin` role's policies cannot be edited, system roles and roles still assigned to users cannot be deleted. `Role` and `Policy` are privileged subjects: whoever may write them can grant themselves anything, so give them only to people you would trust as admins. `GET /auth/me/abilities` returns your effective rules (placeholders resolved) for driving a UI.

- Create the first admin by setting `ADMIN_EMAIL` and `ADMIN_PASSWORD`. Everyone who registers is a `user`.

```bash
curl -X POST :8000/auth/register -H 'content-type: application/json' -d '{"email":"me@example.com","password":"a-long-password"}'
TOKEN=$(curl -s -X POST :8000/auth/login -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"a-long-password"}' | jq -r .access_token)
curl -X POST :8000/todos -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"title":"first"}'
```

## Endpoints
| Method | Path | Access |
|---|---|---|
| GET | `/health`, `/ready` | public |
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | public |
| GET | `/auth/me`, `/auth/me/abilities` | any authenticated user |
| POST / GET | `/todos` | authenticated (list is filtered to what you may read) |
| GET / PATCH / DELETE | `/todos/{id}` | owner or admin (403 otherwise) |
| GET | `/users` | self (user) / everyone (admin) |
| GET / PATCH | `/users/{id}` | self or admin; role changes admin-only |
| DELETE | `/users/{id}` | admin |
| GET / POST / PATCH / DELETE | `/roles`, `/roles/{id}` | `Role` policies (admin by default) |
| GET / POST / PUT | `/roles/{id}/policies` | `Policy` policies (admin by default) |
| GET / PUT / DELETE | `/policies/meta`, `/policies/{id}` | `Policy` policies (admin by default) |
| GET | `/databases` | admin |
| POST | `/tasks/purge-completed?older_than_days=30` | admin; queues purge, returns `task_id` |
| GET | `/tasks/{task_id}` | admin |

## Database configuration
- Set `DATABASE_URL`, or the parts `DB_DRIVER`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (the password is URL-escaped automatically). SQLite is the default.
- Define more connections with `DATABASES='{"tenant_a": "<url>", ...}'`. Send `X-Database: tenant_a` on any request to use that database. Engines are created lazily on first use, tables are created automatically, and `GET /databases` lists the names.
- The chosen name is passed to Celery tasks (`db` argument), so background work runs against the same database.
- The API and workers must be able to reach the same databases. Users, roles, policies and todos are stored per database, and a token is only valid for the database it was issued for.

## Development (SDLC)
`make install` then `make check` (ruff, mypy --strict, pytest with >=85% coverage). See [CONTRIBUTING](CONTRIBUTING.md).

| Phase | Document |
|---|---|
| Requirements | [docs/01-requirements.md](docs/01-requirements.md) |
| Design | [docs/02-architecture.md](docs/02-architecture.md), [ADRs](docs/adr) |
| Testing | [docs/03-testing.md](docs/03-testing.md) |
| Deployment | [docs/04-deployment.md](docs/04-deployment.md) |
| Operations | [docs/05-operations.md](docs/05-operations.md) |
| History | [CHANGELOG.md](CHANGELOG.md), [SECURITY.md](SECURITY.md) |

## Docker / Kubernetes / CI-CD
- `docker compose up --build` runs api, worker, beat, redis and postgres (API on :8000).
- `k8s/`: Kustomize manifests (api, worker, single-instance beat, redis, postgres, ingress). `kubectl apply -k k8s`. Edit the ingress host and replace the placeholder secret in `k8s/config.yaml` first.
- `.github/workflows/ci.yml`: tests and image build on PRs.
- `.github/workflows/cd.yml`: on push to `main`, test, push image to GHCR, then `kubectl apply -k` and wait for rollouts. Needs a `KUBE_CONFIG` secret (base64 kubeconfig) and a `production` environment.
