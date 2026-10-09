# ADR-0002: Named database registry selected per request
Status: Accepted

**Context** Some deployments need several databases (tenants, environments) behind one API.

**Decision** Operators define named URLs in `DATABASES`; clients select by name with `X-Database`. Engines are created lazily, cached, and tables created on first use. The name travels to Celery tasks.

**Consequences** Clients cannot inject connection strings. Every API/worker pod must reach every configured database. Adding authentication later should bind allowed names to the caller.
