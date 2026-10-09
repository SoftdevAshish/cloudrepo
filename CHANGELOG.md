# Changelog
Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

## [0.4.0]
### Added
- Dynamic roles and policies: `role` / `policy` tables, `/roles`, `/roles/{id}/policies`, `/policies/{id}`, `/policies/meta`; rules apply on the next request.
- `${user.id|email|role|is_active}` placeholders in policy conditions; rule validation against model columns.
- `GET /auth/me/abilities`.
- Roles are seeded per database (`admin` immutable, `user` editable). Existing 0.3.x databases upgrade automatically.

### Changed
- Abilities are built from stored policies instead of code. Default `user` policies are equivalent to the previous hard-coded rules.
- `PATCH /users/{id}` accepts any existing role name (was limited to `admin`/`user`); unknown roles return 422.

## [0.3.0]
### Added
- User registration/login with JWT access and refresh tokens (bcrypt hashing, database-bound tokens).
- CASL-style authorization (`app/core/casl.py`): roles `user` and `admin`, ownership conditions, field-level rules, SQL filtering of lists.
- `/users` management endpoints; admin bootstrap via `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
- NestJS-style modules (controller / service / repository per feature).

### Changed
- **BREAKING:** all `/todos`, `/databases` and `/tasks/*` endpoints require authentication; `/databases` and `/tasks/*` are admin-only.
- **BREAKING:** todos now have an `owner_id`. Databases created by 0.2.x must be recreated or migrated manually.
- **BREAKING:** Celery task names are now `todos.notify_created` and `todos.purge_completed`; drain old queues before upgrading.
- Production refuses to start with a placeholder `JWT_SECRET_KEY`.
- SQLite `DB_NAME` may be an absolute path.

## [0.2.0]
### Added
- Dynamic database configuration (URL or parts) and per-request database selection via `X-Database`.
- `/health` and `/ready` endpoints; Kubernetes probes use them.
- Lint/typing/coverage tooling, pre-commit, Makefile, SDLC documentation, issue/PR templates, Dependabot.

## [0.1.0]
### Added
- Todo CRUD API (FastAPI, SQLModel/SQLAlchemy), Celery tasks and schedule, Docker, Kubernetes, CI/CD.
