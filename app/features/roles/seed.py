"""Default roles, created idempotently whenever a database is first used.

Only *missing* roles are created, so edits made later through the API are never overwritten.
The admin role is the exception: its single `manage all` policy is re-asserted on every start so
a database can never end up with no way to administer it.
"""

import logging
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.casl import ALL, Action
from app.features.roles.models import ADMIN_ROLE, USER_ROLE, Policy, Role
from app.features.roles.repository import RolesRepository

logger = logging.getLogger(__name__)

USER_POLICIES: list[dict[str, Any]] = [
    {"action": Action.MANAGE, "subject": "Todo", "conditions": {"owner_id": "${user.id}"}},
    {"action": Action.READ, "subject": "User", "conditions": {"id": "${user.id}"}},
    {"action": Action.UPDATE, "subject": "User", "conditions": {"id": "${user.id}"}},
    {"action": Action.UPDATE, "subject": "User", "fields": ["role", "is_active"], "inverted": True},
]


def _ensure_role(repo: RolesRepository, name: str, description: str) -> tuple[Role, bool]:
    role = repo.get_by_name(name)
    if role is not None:
        return role, False
    try:
        return repo.save(Role(name=name, description=description, is_system=True)), True
    except IntegrityError:  # another process seeded it first
        repo.session.rollback()
        role = repo.get_by_name(name)
        assert role is not None  # noqa: S101
        return role, False


def seed_defaults(engine: Engine) -> None:
    with Session(engine) as session:
        repo = RolesRepository(session)
        admin, _ = _ensure_role(repo, ADMIN_ROLE, "Full access")
        rules = repo.policies(admin.id)  # type: ignore[arg-type]
        if len(rules) != 1 or (rules[0].action, rules[0].subject, rules[0].inverted) != (
            Action.MANAGE,
            ALL,
            False,
        ):
            repo.replace_policies(
                admin.id,  # type: ignore[arg-type]
                [Policy(role_id=admin.id, action=Action.MANAGE, subject=ALL)],  # type: ignore[arg-type]
            )
        user, created = _ensure_role(repo, USER_ROLE, "Default role for registered users")
        if created:
            repo.replace_policies(
                user.id,  # type: ignore[arg-type]
                [Policy(role_id=user.id, **spec) for spec in USER_POLICIES],  # type: ignore[arg-type]
            )
            logger.info("Seeded default roles")
