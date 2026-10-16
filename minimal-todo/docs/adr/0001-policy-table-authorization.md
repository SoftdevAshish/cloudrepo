# ADR 0001: Authorization as a policy table

- Status: accepted
- Context: Users must only touch their own todos; admins everything. We could scatter `if todo.owner_id != user.id` through routes, use fixed role checks, or describe permissions as data.
- Decision: Keep permissions in one declarative table (`POLICIES`) evaluated by a tiny engine (`can`, `scope`, `authorize`) with **default deny**. Routes only ask the engine.
- Consequences:
  - (+) One place to audit and change permissions; easy to unit test without HTTP.
  - (+) List endpoints get the same rule as a SQL filter, so they cannot leak rows.
  - (-) Slightly more code than inline checks for a two-role app.
  - (-) Conditions are limited to `own` / `any`; richer rules (teams, field-level) need the engine extended. The larger project in `../../app/core/casl.py` shows a fuller version stored in the database.
