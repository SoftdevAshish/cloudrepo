# 3. Testing Strategy

| Level | Tooling | Scope |
|---|---|---|
| Unit | pytest | CASL library and config (`tests/core/`) |
| Migration | pytest + temp SQLite | models and migrations agree (drift guard), idempotent upgrade, downgrade, adopting pre-Alembic databases (`tests/core/test_migrations.py`) |
| Integration | pytest + FastAPI TestClient + in-memory SQLite, Celery eager | every endpoint, DB selection, tasks end-to-end |
| Static | ruff (lint + format + bandit rules), mypy `--strict` | whole `app/` |
| Security | pip-audit, detect-private-key hook | dependencies, secrets |
| Build | `docker build` in CI | image builds |

Tests are organised per feature: `tests/{auth,todos,users,roles,system,core}/`, sharing fixtures from `tests/conftest.py`.

Quality gate (CI and `make check`): lint, typecheck, tests with coverage >= 85%.

## Requirement traceability
| Requirement | Tests |
|---|---|
| FR-1..FR-5 | `tests/todos/` |
| FR-6 | `test_notify_task` |
| FR-7 | `test_purge_task`, `test_trigger_purge_endpoint` |
| FR-9 | `test_runtime_database_selection`, `test_token_is_bound_to_its_database`, `tests/core/test_config.py` |
| FR-10 | `tests/auth/` |
| FR-11 | `test_users_only_see_their_own_todos`, `test_owner_is_taken_from_token_not_payload` |
| FR-12 | `test_admin_manages_everything`, `test_admin_can_change_roles`, `test_only_admin_deletes_users...` |
| FR-13 | `test_field_level_rule_blocks_privilege_escalation` |
| FR-14 | `test_ops_endpoints_are_admin_only` |
| FR-15 | manual (startup seed); see smoke test in `docs/05-operations.md` |
| NFR-7 | `test_login_failures_are_indistinguishable`, `test_production_rejects_weak_jwt_secret` |
| FR-16..FR-17 | `test_editing_a_policy_changes_access_immediately`, `test_new_role_assigned_to_user`, `test_cannot_rule_overrides_earlier_can`, `test_replace_policies_is_atomic`, `test_roles_are_per_database` |
| FR-18 | `test_invalid_policies_are_rejected`, `test_condition_values_are_bound...`, `test_admin_role_is_protected`, `test_invalid_stored_policy_is_skipped_not_fatal` |
| FR-19 | `test_assigning_unknown_role_is_rejected`, `test_system_and_in_use_roles_cannot_be_deleted` |
| NFR-8 | `tests/core/test_casl.py` |
| NFR-1 | `test_health_and_ready_are_public` |

Not covered by automation: real Redis/Postgres runs and the Kubernetes deploy (verified manually per `docs/04-deployment.md`).
