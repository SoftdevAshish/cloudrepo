# 1. Requirements (SDLC phase: Requirements)

## Purpose
A small, secure Todo API where every user manages their own todos, and administrators can manage everyone's.

## Actors
| Actor | Description |
|---|---|
| Anonymous | Not signed in. May only register, log in and call `/health`. |
| User | Registered person (role `user`). |
| Admin | Registered person whose email is in `ADMIN_EMAILS` (role `admin`). |

## Functional requirements
Every requirement has an ID so that design, code and tests can point back to it (see traceability below).

### Authentication
| ID | Requirement | Acceptance criteria |
|---|---|---|
| REQ-AUTH-1 | A person can register with email and password | 201 and the user (no password fields) is returned; duplicate email gives 409; password shorter than 8 characters gives 422 |
| REQ-AUTH-2 | A registered user can log in | Correct credentials give a signed, expiring access token; wrong password and unknown email give the **same** 401 response |
| REQ-AUTH-3 | Protected endpoints require a valid token | Missing, malformed, expired or unknown-user tokens give 401 |
| REQ-AUTH-4 | A user can view their own profile | `GET /auth/me` returns id, email and role |

### Todo CRUD
| ID | Requirement | Acceptance criteria |
|---|---|---|
| REQ-TODO-1 | Create a todo | Title 1-200 chars, optional description; owner is the caller; `done` defaults to false |
| REQ-TODO-2 | Read one todo | 200, or 404 if it does not exist |
| REQ-TODO-3 | List todos | Filter by `done`; pagination with `skip`/`limit` (limit 1-100) |
| REQ-TODO-4 | Update a todo (partial) | Only the fields sent change; `updated_at` is refreshed; the owner cannot be changed |
| REQ-TODO-5 | Delete a todo | 204; afterwards the todo is 404 |
| REQ-TODO-6 | Input is validated | Invalid input gives 422 with details |

### Authorization (policy based)
| ID | Requirement | Acceptance criteria |
|---|---|---|
| REQ-AUTHZ-1 | A `user` may create/read/update/delete **only their own** todos | Other people's todos give 403 and are never changed |
| REQ-AUTHZ-2 | An `admin` may manage **all** todos | Admin can read, edit, delete and list any todo |
| REQ-AUTHZ-3 | Default deny | A role with no matching policy is refused (403) and sees an empty list |
| REQ-AUTHZ-4 | Lists contain only permitted rows | A user's list never includes other users' todos |

## Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-SEC-1 | Passwords stored only as bcrypt hashes; never returned or logged |
| NFR-SEC-2 | Secrets (JWT key, DB URL) come from environment variables, not code |
| NFR-SEC-3 | Tokens expire (default 30 minutes) |
| NFR-QUAL-1 | Automated tests for every requirement; lint clean; CI on every push |
| NFR-MAINT-1 | Permissions are data (one policy table), not scattered `if` statements |

## Out of scope (for this minimal version)
Refresh tokens, password reset, email verification, rate limiting, database migrations, multi-tenancy. They are listed in the roadmap in `README.md`.

## Traceability matrix
| Requirement | Code | Tests |
|---|---|---|
| REQ-AUTH-1 | `routers/auth.py::register` | `test_auth.py::test_register_*`, `test_duplicate_email_conflict`, `test_weak_password_rejected` |
| REQ-AUTH-2 | `routers/auth.py::login`, `security.py` | `test_login_wrong_password_and_unknown_user_look_identical` |
| REQ-AUTH-3 | `deps.py::get_current_user` | `test_missing_or_bad_token_is_401`, `test_token_for_deleted_user_is_401` |
| REQ-AUTH-4 | `routers/auth.py::me` | `test_login_success_and_me` |
| REQ-TODO-1..6 | `routers/todos.py`, `schemas.py` | `test_todos.py` (CRUD section) |
| REQ-AUTHZ-1..4 | `policies.py` | `test_todos.py` (policy section), `test_policies.py` |
| NFR-SEC-1/3 | `security.py` | `test_register_returns_user_without_password` |
