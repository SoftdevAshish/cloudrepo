# ADR-0004: JWT authentication and CASL-style authorization
Status: Accepted

**Context** The API needs per-user ownership and role-based access, with rules that are easy to audit and test. The team is familiar with NestJS conventions (modules, guards, CASL).

**Decision**
- Stateless JWT bearer auth (PyJWT, HS256) with access and refresh tokens; bcrypt for passwords.
- A small in-repo CASL equivalent (`app/core/casl.py`) because there is no maintained Python CASL port: abilities with conditions, fields, inversion, and `accessible_by` to compile rules into SQL.
- NestJS-style module layout: controller -> service -> repository; guards as FastAPI dependencies.
- Tokens carry the database name they were issued for.

**Alternatives considered** Casbin/Oso (policy languages and heavier runtime, harder to colocate with ORM filtering); session cookies (state and CSRF concerns for an API); asymmetric JWT (unneeded until another service verifies tokens).

**Consequences** Rules live in code and ship with the app. Refresh tokens cannot be revoked before expiry (mitigation: short lifetimes; add a token table/denylist if needed). Changing `JWT_SECRET_KEY` logs everyone out. Adding `owner_id` to `todo` is a breaking schema change: databases created by 0.2.x must be recreated or migrated by hand (see ADR-0003).
