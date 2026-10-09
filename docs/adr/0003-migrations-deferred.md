# ADR-0003: Schema migrations deferred
Status: Superseded by ADR-0006

**Context** Tables are currently created with `create_all`, which cannot alter existing tables.

**Decision** Accept `create_all` for the initial schema. Introduce Alembic before the first schema change in production.

**Consequences** A schema change without migrations would require manual DDL; this ADR is the reminder to add Alembic first.
