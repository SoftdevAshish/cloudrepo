# Todo API: FastAPI + SQLModel/SQLAlchemy + Celery

## Run
```bash
pip install -r requirements.txt
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

Set `DATABASE_URL` for Postgres etc. (the same DB must be reachable by API and worker; SQLite works for local dev).

## Tests
`pytest` (Celery runs eagerly, in-memory SQLite).

## Docker / Kubernetes / CI-CD
- `docker compose up --build` runs api, worker, beat, redis and postgres (API on :8000).
- `k8s/`: Kustomize manifests (api, worker, single-instance beat, redis, postgres, ingress). `kubectl apply -k k8s`. Edit the ingress host and replace the placeholder secret in `k8s/config.yaml` first.
- `.github/workflows/ci.yml`: tests and image build on PRs.
- `.github/workflows/cd.yml`: on push to `main`, test, push image to GHCR, then `kubectl apply -k` and wait for rollouts. Needs a `KUBE_CONFIG` secret (base64 kubeconfig) and a `production` environment.
