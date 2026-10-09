# 5. Operations Runbook

| Symptom | Check | Action |
|---|---|---|
| Pod not Ready | `kubectl -n todo logs deploy/api`; `/ready` returns 503 | Database unreachable: check `DATABASE_URL`, postgres pod, network policy |
| Tasks stay PENDING | `kubectl -n todo logs deploy/worker`; Redis reachable? | Restart worker; verify `CELERY_BROKER_URL` |
| Scheduled purge not running | Exactly one `beat` pod? | Scale beat to 1 (never more) |
| 400 Unknown database | `GET /api/v1/databases` | Add the name to `DATABASES` and restart |
| App crash-loops at startup with a JWT_SECRET_KEY error | Pod logs | Set a real secret (>= 32 chars, not `change-me*`) |
| Everyone gets 401 after a deploy | Was `JWT_SECRET_KEY` changed? | Expected: changing the secret invalidates all tokens; users log in again |
| Locked out of admin | | Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` for a *new* email and restart (the `admin` role's `manage all` rule is re-created on every start), or set `user.role='admin'` in the DB |
| A user can do too much / too little | `GET /api/v1/auth/me/abilities` as that user; `GET /api/v1/roles/{id}/policies` | Fix the role's policies; effective on the next request |
| Policy ignored | App log: `Skipping invalid policy id=...` | A stored rule no longer validates (e.g. renamed column); replace it via `PUT /api/v1/policies/{id}` |
| Deploy fails at the migrate step | `kubectl -n todo logs job/migrate` | Fix the migration or database reachability and redeploy; the rollout never started |
| Pods crash with `no such table` / `relation does not exist` | `AUTO_MIGRATE=false` and the Job didn't run | Run `kubectl apply -k k8s/migrate` or `python -m scripts.migrate` |
| New named database fails on first use | App log | With `AUTO_MIGRATE=false`, run `python -m scripts.migrate <name>` before using it |

## Monitoring (recommended)
Scrape probes at `/health` and `/ready`; alert on rollout failures and worker queue depth in Redis.
