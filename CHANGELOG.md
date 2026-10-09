# Changelog
Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

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
