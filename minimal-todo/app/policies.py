"""Policy-based authorization.

Permissions are DATA (the POLICIES table), not if-statements scattered through routes.
Each policy says: which role, which actions, on which resource, under which condition.

    condition "any"  -> the action is allowed on every instance
    condition "own"  -> allowed only when instance.owner_id == user.id

Rules are default-deny: if no policy matches, the answer is "not allowed".
Routes ask two questions:
    can(user, action, obj)      -> may this user perform this action on THIS object?
    scope(user, action, stmt)   -> restrict a list query to the rows the user may access
"""

from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException, status
from sqlmodel.sql.expression import SelectOfScalar

from app.models import Todo, User


class Action(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


@dataclass(frozen=True)
class Policy:
    role: str
    actions: frozenset[str]  # use {"*"} for all actions
    resource: str
    condition: str = "own"  # "own" | "any"


ALL = frozenset({"*"})
CRUD = frozenset(a.value for a in Action)

POLICIES: tuple[Policy, ...] = (
    Policy(role="user", actions=CRUD, resource="todo", condition="own"),
    Policy(role="admin", actions=ALL, resource="todo", condition="any"),
)


def _matching(user: User, action: Action, resource: str) -> list[Policy]:
    return [
        p
        for p in POLICIES
        if p.role == user.role
        and p.resource == resource
        and ("*" in p.actions or action.value in p.actions)
    ]


def can(user: User, action: Action, obj: Todo | None = None) -> bool:
    """Instance-level check. With obj=None, asks whether the user may ever do the action."""
    for policy in _matching(user, action, "todo"):
        if policy.condition == "any" or obj is None or obj.owner_id == user.id:
            return True
    return False


def scope(user: User, action: Action, stmt: SelectOfScalar[Todo]) -> SelectOfScalar[Todo]:
    """Filter a SELECT so it only returns rows this user may access (default-deny)."""
    matches = _matching(user, action, "todo")
    if any(p.condition == "any" for p in matches):
        return stmt
    if matches:
        return stmt.where(Todo.owner_id == user.id)  # type: ignore[arg-type]
    return stmt.where(False)  # type: ignore[arg-type]


def authorize(user: User, action: Action, obj: Todo | None = None) -> None:
    if not can(user, action, obj):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
