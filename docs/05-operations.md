# 5. Operations Runbook

| Symptom | Check | Action |
|---|---|---|
| Pod not Ready | `kubectl -n todo logs deploy/api`; `/ready` returns 503 | Database unreachable: check `DATABASE_URL`, postgres pod, network policy |
| Tasks stay PENDING | `kubectl -n todo logs deploy/worker`; Redis reachable? | Restart worker; verify `CELERY_BROKER_URL` |
| Scheduled purge not running | Exactly one `beat` pod? | Scale beat to 1 (never more) |
| 400 Unknown database | `GET /databases` | Add the name to `DATABASES` and restart |
| Migration needed | See ADR-0003 | Add Alembic before changing the schema |

## Monitoring (recommended)
Scrape probes at `/health` and `/ready`; alert on rollout failures and worker queue depth in Redis.
