# ADR-0006: Feature-based layout, `/api/v1`, and Alembic migrations
Status: Accepted (supersedes ADR-0003)

**Context** The project grew auth, users, roles and todos. A flat `modules/` package, unversioned URLs and `create_all` (which cannot alter tables) would make every later change risky.

**Decision**
- `app/features/<feature>/` holds each feature end to end (controller, service, repository, models, schemas); `app/core/` holds cross-cutting code; `app/api/` assembles routers. The API is versioned: routes live under `/api/v1`; health probes stay unversioned.
- Schema is owned by Alembic (`migrations/`). `env.py` can target any configured database (`-x db=<name>`) or a connection supplied by the app, so named databases and the default one use the same revisions.
- `AUTO_MIGRATE` (default on) upgrades a database on first use for development and on-the-fly databases; production turns it off and runs `python -m scripts.migrate` in a Kubernetes Job before rolling out.
- The initial revision creates only missing tables, which adopts databases built by `create_all` in releases <= 0.4.
- A test compares migrated schema to the models so drift is caught in CI.

**Consequences**
- All URLs gained the `/api/v1` prefix (breaking for existing clients).
- Every model change needs a reviewed migration; migrations must be backward compatible with the previous release because rollouts overlap.
- Tests still build schemas with `create_all` for speed; the migration tests cover the Alembic path.
