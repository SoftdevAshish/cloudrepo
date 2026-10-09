# Changelog
Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

## [0.2.0]
### Added
- Dynamic database configuration (URL or parts) and per-request database selection via `X-Database`.
- `/health` and `/ready` endpoints; Kubernetes probes use them.
- Lint/typing/coverage tooling, pre-commit, Makefile, SDLC documentation, issue/PR templates, Dependabot.

## [0.1.0]
### Added
- Todo CRUD API (FastAPI, SQLModel/SQLAlchemy), Celery tasks and schedule, Docker, Kubernetes, CI/CD.
