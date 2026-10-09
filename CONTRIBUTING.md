# Contributing

## Workflow
1. Branch from `main`: `feat/<topic>`, `fix/<topic>`.
2. `make install` (installs dev tools and pre-commit hooks).
3. Make small, focused commits using [Conventional Commits](https://www.conventionalcommits.org) (`feat:`, `fix:`, `docs:`, `chore:`).
4. `make check` must pass (lint, mypy strict, tests, coverage >= 85%).
5. Changed a model? Add a migration (`make migrate && make revision m="..."`), review it, keep it backward compatible. CI fails if models and migrations differ.
6. Add/adjust tests and docs (`docs/`), update `CHANGELOG.md` under *Unreleased*; record significant decisions as an ADR.
7. Open a PR using the template; at least one approval required; CI must be green.

## Definition of done
Tests added (in the matching `tests/<feature>/` folder), migration included for model changes, docs updated, no new lint/type errors, no secrets, deployment impact noted in the PR.
