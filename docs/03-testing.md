# 3. Testing Strategy

| Level | Tooling | Scope |
|---|---|---|
| Unit | pytest | CASL library (`test_casl.py`), config |
| Integration | pytest + FastAPI TestClient + in-memory SQLite, Celery eager | every endpoint, DB selection, tasks end-to-end |
| Static | ruff (lint + format + bandit rules), mypy `--strict` | whole `app/` |
| Security | pip-audit, detect-private-key hook | dependencies, secrets |
| Build | `docker build` in CI | image builds |

Quality gate (CI and `make check`): lint, typecheck, tests with coverage >= 85%.

## Requirement traceability
| Requirement | Tests |
|---|---|
| FR-1..FR-5 | `tests/test_todos.py` |
| FR-6 | `test_notify_task` |
| FR-7 | `test_purge_task`, `test_trigger_purge_endpoint` |
| FR-9 | `test_runtime_database_selection`, `test_token_is_bound_to_its_database`, `tests/test_config.py` |
| FR-10 | `tests/test_auth.py` |
| FR-11 | `test_users_only_see_their_own_todos`, `test_owner_is_taken_from_token_not_payload` |
| FR-12 | `test_admin_manages_everything`, `test_admin_can_change_roles`, `test_only_admin_deletes_users...` |
| FR-13 | `test_field_level_rule_blocks_privilege_escalation` |
| FR-14 | `test_ops_endpoints_are_admin_only` |
| FR-15 | manual (startup seed); see smoke test in `docs/05-operations.md` |
| NFR-7 | `test_login_failures_are_indistinguishable`, `test_production_rejects_weak_jwt_secret` |
| NFR-8 | `tests/test_casl.py` |
| NFR-1 | `test_health_and_ready_are_public` |

Not covered by automation: real Redis/Postgres runs and the Kubernetes deploy (verified manually per `docs/04-deployment.md`).
