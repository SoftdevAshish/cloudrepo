# 1. Requirements (SDLC: Planning & Analysis)

## Purpose
A small, production-grade backend for managing todo items, with background processing.

## Stakeholders
| Role | Interest |
|---|---|
| API consumers (web/mobile clients) | Stable, documented CRUD API |
| Operators / SRE | Observable, deployable, scalable service |
| Developers | Fast feedback, clear conventions |

## Functional requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Create a todo (title required, 1-200 chars; optional description) | Must |
| FR-2 | List todos with `completed` filter and `offset`/`limit` pagination (limit <= 500) | Must |
| FR-3 | Read a single todo by id (404 when absent) | Must |
| FR-4 | Partially update a todo; `updated_at` refreshed | Must |
| FR-5 | Delete a todo | Must |
| FR-6 | After creation, a background notification task is queued | Should |
| FR-7 | Completed todos untouched for N days (default 30) are purged daily and on demand | Should |
| FR-8 | Task status can be queried by id | Should |
| FR-9 | Database selectable by config and per request (`X-Database`) | Could |
| FR-10 | Users register and log in with email + password; receive short-lived access and longer-lived refresh JWTs | Must |
| FR-11 | Todos are owned by their creator; users can only see and change their own | Must |
| FR-12 | Admins can manage all users and todos, change roles and deactivate users | Must |
| FR-13 | Users cannot escalate privileges (`role`, `is_active` are admin-only fields) | Must |
| FR-14 | Operational endpoints (`/api/v1/databases`, `/api/v1/tasks/*`) are admin-only | Must |
| FR-16 | Administrators create roles and edit each role's policies at runtime through the API; changes apply to the next request without redeploying | Must |
| FR-17 | Policies support conditions with `${user.*}` placeholders, field restrictions and deny rules | Must |
| FR-18 | Invalid or unsafe policies are rejected; the `admin` role cannot be locked out or modified | Must |
| FR-19 | Assigning a user to a role validates the role exists; roles in use cannot be deleted | Must |
| FR-15 | The first administrator can be bootstrapped from configuration | Should |

## Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-1 | Liveness (`/health`) and readiness (`/ready`) endpoints |
| NFR-2 | Configuration only via environment variables (12-factor); no secrets in the repo |
| NFR-3 | Horizontally scalable stateless API and workers; exactly one scheduler (beat) |
| NFR-4 | Automated quality gate: lint, strict typing, tests with >= 85% coverage, dependency audit |
| NFR-5 | Reproducible container image; non-root runtime user |
| NFR-6 | Input validated at the boundary; unknown database names rejected |
| NFR-7 | Passwords stored only as bcrypt hashes; login does not reveal whether an email exists; production refuses to start with a weak JWT secret |
| NFR-8 | Authorization rules are declared in one place and enforced at class, instance and field level |

## Out of scope (current release)
Refresh-token revocation/rotation, rate limiting and account lockout, email verification and password reset, sharing todos between users, schema migrations tooling (see ADR-0003).

## Acceptance
Each FR maps to automated tests in `tests/` (see `docs/03-testing.md`).
