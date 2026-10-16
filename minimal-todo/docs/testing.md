# 3. Testing (SDLC phase: Testing / Verification)

| Level | Where | What it proves |
|---|---|---|
| Unit | `tests/test_policies.py` | The policy engine decides correctly with no HTTP or DB |
| Integration (API) | `tests/test_auth.py`, `tests/test_todos.py` | Real requests through FastAPI, auth, policies and an in-memory SQLite database |
| Static analysis | `ruff check` | Style, bugs, common security smells (flake8-bandit rules) |
| Format | `ruff format --check` | Consistent formatting |

Run everything: `make test` and `make lint`. CI runs both on every push and pull request.

## Strategy
- **Every requirement ID has at least one test** (see the traceability matrix in `requirements.md`).
- **Negative tests are mandatory for security**: wrong password, bad token, other user's todo, unknown role.
- Each test gets a fresh in-memory database, so tests are independent and fast (about 1 second for the suite).
- Bcrypt cost is lowered to 4 in tests only (`BCRYPT_ROUNDS`), never in production defaults.

## Definition of done for a change
1. Requirement written (ID and acceptance criteria).
2. Tests written or updated; they fail without the change.
3. `make lint` and `make test` pass.
4. Docs updated (requirements, design, ADR if a decision changed).
5. Reviewed via pull request; CI green.
