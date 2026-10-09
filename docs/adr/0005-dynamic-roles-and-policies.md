# ADR-0005: Roles and policies stored in the database
Status: Accepted (supersedes the "rules are code" part of ADR-0004)

**Context** Hard-coded rules need a deploy for every access change. Operators want to create roles and adjust permissions at runtime.

**Decision** Store roles and CASL rules (`role`, `policy` tables, JSON conditions/fields). Build each request's `Ability` from the user's role policies, with `${user.*}` placeholders resolved per user. Validate every rule against an explicit registry of subjects and columns before it is stored (and again when loaded). Seed `admin` (immutable `manage all`) and `user` (editable defaults) per database. One role per user.

**Alternatives considered** Casbin/OPA (separate policy language and runtime, harder to push row filters into SQL); a fixed permission-flag matrix (cannot express ownership or field rules); caching abilities (faster, but stale across pods without an invalidation channel).

**Consequences**
- One extra indexed query per authenticated request; add a short-TTL or pub/sub-invalidated cache if this shows up in profiles.
- `Role`/`Policy` write access is equivalent to full control; treat it as admin-level.
- Roles are per database, like users.
- Single role per user keeps reasoning simple; multiple roles would be a union of policy lists if needed later.
- 0.3.x databases upgrade in place: new tables are created and roles seeded at startup; existing `user.role` values (`admin`/`user`) map onto the seeded roles.
