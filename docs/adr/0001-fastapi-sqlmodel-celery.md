# ADR-0001: FastAPI + SQLModel + Celery
Status: Accepted

**Context** We need a typed, documented HTTP API with reliable background jobs and scheduling.

**Decision** FastAPI for HTTP (OpenAPI for free), SQLModel on SQLAlchemy 2 for models/ORM, Celery with Redis for tasks and beat.

**Consequences** Sync SQLAlchemy sessions are shared by API and workers (simple, one code path). Redis becomes a required runtime dependency.
