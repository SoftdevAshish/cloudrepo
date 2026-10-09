"""What policies may talk about, and validation so stored rules are always safe to compile.

Policies are data written by administrators. Before one is stored, its subject, fields and
condition keys are checked against real model columns (so they can never reach arbitrary
attributes), operators come from an allow-list, and values are bound as SQL parameters.
"""

import re
from typing import Any

from sqlmodel import SQLModel

from app.core.casl import ALL, Action
from app.features.auth.constants import SYSTEM
from app.features.roles.models import Policy, Role
from app.features.todos.models import Todo
from app.features.users.models import User

SUBJECT_MODELS: dict[str, type[SQLModel] | None] = {
    ALL: None,
    SYSTEM: None,
    "Todo": Todo,
    "User": User,
    "Role": Role,
    "Policy": Policy,
}
SENSITIVE_FIELDS = {"hashed_password"}
OPERATORS = {"$eq", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte"}
LIST_OPERATORS = {"$in", "$nin"}
USER_ATTRIBUTES = ("id", "email", "role", "is_active")
PLACEHOLDER = re.compile(r"^\$\{user\.(" + "|".join(USER_ATTRIBUTES) + r")\}$")
MAX_CONDITIONS = 10
MAX_LIST = 100


def allowed_fields(subject: str) -> list[str]:
    model = SUBJECT_MODELS.get(subject)
    if model is None:
        return []
    return sorted(set(model.__table__.columns.keys()) - SENSITIVE_FIELDS)  # type: ignore[attr-defined]


def describe() -> dict[str, Any]:
    """Metadata for building a policy editor UI."""
    return {
        "actions": [a.value for a in Action],
        "subjects": {name: allowed_fields(name) for name in SUBJECT_MODELS},
        "operators": sorted(OPERATORS),
        "placeholders": [f"${{user.{a}}}" for a in USER_ATTRIBUTES],
    }


def _check_scalar(value: Any) -> None:
    if isinstance(value, str):
        if value.startswith("${") and not PLACEHOLDER.match(value):
            raise ValueError(
                f"unknown placeholder {value!r}; allowed: {describe()['placeholders']}"
            )
    elif not (value is None or isinstance(value, bool | int | float)):
        raise ValueError(f"unsupported condition value {value!r}")


def validate_rule(
    action: str, subject: str, conditions: dict[str, Any] | None, fields: list[str] | None
) -> None:
    """Raise ValueError if the rule is not safe/meaningful. Used on write and when loading."""
    if action not in {a.value for a in Action}:
        raise ValueError(f"unknown action {action!r}")
    if subject not in SUBJECT_MODELS:
        raise ValueError(f"unknown subject {subject!r}; allowed: {sorted(SUBJECT_MODELS)}")
    columns = set(allowed_fields(subject))
    if SUBJECT_MODELS[subject] is None and (conditions or fields):
        raise ValueError(f"subject {subject!r} does not support conditions or fields")
    if fields is not None and (not fields or not set(fields) <= columns):
        raise ValueError(f"fields must be a non-empty subset of {sorted(columns)}")
    if conditions is None:
        return
    if not conditions or len(conditions) > MAX_CONDITIONS:
        raise ValueError(f"conditions must have 1..{MAX_CONDITIONS} entries")
    for name, expected in conditions.items():
        if name not in columns:
            raise ValueError(f"condition field {name!r} is not one of {sorted(columns)}")
        if isinstance(expected, dict):
            if not expected or not set(expected) <= OPERATORS:
                raise ValueError(f"operators must be a subset of {sorted(OPERATORS)}")
            for op, arg in expected.items():
                if op in LIST_OPERATORS:
                    if not isinstance(arg, list) or len(arg) > MAX_LIST:
                        raise ValueError(f"{op} needs a list of at most {MAX_LIST} values")
                    for item in arg:
                        _check_scalar(item)
                else:
                    _check_scalar(arg)
        else:
            _check_scalar(expected)
