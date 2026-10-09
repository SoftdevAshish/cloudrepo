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

## Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/todos` | Create (also queues `notify_todo_created`) |
| GET | `/todos?completed=&offset=&limit=` | List / filter |
| GET | `/todos/{id}` | Read |
| PATCH | `/todos/{id}` | Partial update |
| DELETE | `/todos/{id}` | Delete |
| POST | `/tasks/purge-completed?older_than_days=30` | Queue purge task, returns `task_id` |
| GET | `/tasks/{task_id}` | Celery task status/result |

## Database configuration
- Set `DATABASE_URL`, or the parts `DB_DRIVER`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (the password is URL-escaped automatically). SQLite is the default.
- Define more connections with `DATABASES='{"tenant_a": "<url>", ...}'`. Send `X-Database: tenant_a` on any request to use that database. Engines are created lazily on first use, tables are created automatically, and `GET /databases` lists the names.
- The chosen name is passed to Celery tasks (`db` argument), so background work runs against the same database.
- The API and workers must be able to reach the same databases.

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
