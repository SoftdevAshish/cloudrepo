# 3. Testing Strategy

| Level | Tooling | Scope |
|---|---|---|
| Unit | pytest | config URL building, tasks |
| Integration | pytest + FastAPI TestClient + in-memory SQLite, Celery eager | every endpoint, DB selection, tasks end-to-end |
| Static | ruff (lint + format + bandit rules), mypy `--strict` | whole `app/` |
| Security | pip-audit, detect-private-key hook | dependencies, secrets |
| Build | `docker build` in CI | image builds |

Quality gate (CI and `make check`): lint, typecheck, tests with coverage >= 85%.

## Requirement traceability
| Requirement | Tests |
|---|---|
| FR-1..FR-5 | `test_crud_flow`, `test_validation`, `test_not_found_paths`, `test_pagination` |
| FR-6 | `test_notify_task` |
| FR-7 | `test_purge_task`, `test_trigger_purge_endpoint` |
| FR-9 | `test_runtime_database_selection`, `tests/test_config.py` |
| NFR-1 | `test_health_and_ready` |

Not covered by automation: real Redis/Postgres runs and the Kubernetes deploy (verified manually per `docs/04-deployment.md`).
