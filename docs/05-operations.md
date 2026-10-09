# 5. Operations Runbook

| Symptom | Check | Action |
|---|---|---|
| Pod not Ready | `kubectl -n todo logs deploy/api`; `/ready` returns 503 | Database unreachable: check `DATABASE_URL`, postgres pod, network policy |
| Tasks stay PENDING | `kubectl -n todo logs deploy/worker`; Redis reachable? | Restart worker; verify `CELERY_BROKER_URL` |
| Scheduled purge not running | Exactly one `beat` pod? | Scale beat to 1 (never more) |
| 400 Unknown database | `GET /databases` | Add the name to `DATABASES` and restart |
| App crash-loops at startup with a JWT_SECRET_KEY error | Pod logs | Set a real secret (>= 32 chars, not `change-me*`) |
| Everyone gets 401 after a deploy | Was `JWT_SECRET_KEY` changed? | Expected: changing the secret invalidates all tokens; users log in again |
| Locked out of admin | | Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` for a *new* email and restart, or update `role` in the DB |
| Migration needed | See ADR-0003 | Add Alembic before changing the schema |

## Monitoring (recommended)
Scrape probes at `/health` and `/ready`; alert on rollout failures and worker queue depth in Redis.
