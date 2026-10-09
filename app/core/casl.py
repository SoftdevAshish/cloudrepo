"""A small CASL-style authorization library (https://casl.js.org).

Rules are declared with `AbilityBuilder.can` / `cannot`, optionally restricted by
`conditions` (a MongoDB-like dict, matched against instances or turned into SQL) and
`fields`. Later rules override earlier ones. Checking against a class (or its name)
answers "could the user ever do this?"; checking against an instance also evaluates
conditions.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sqlalchemy import and_, false, not_, or_, true
from sqlalchemy.sql.elements import ColumnElement

ALL = "all"


class Action(StrEnum):
    MANAGE = "manage"  # wildcard: any action
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class ForbiddenError(Exception):
    def __init__(self, action: str, subject: str, field: str | None = None) -> None:
        self.action, self.subject, self.field = str(action), subject, field
        target = f"{subject}.{field}" if field else subject
        super().__init__(f"Cannot {self.action} {target}")


@dataclass(frozen=True)
class Rule:
    action: str
    subject: str
    conditions: Mapping[str, Any] | None = None
    fields: tuple[str, ...] | None = None
    inverted: bool = False


def subject_name(subject: object) -> str:
    if isinstance(subject, str):
        return subject
    if isinstance(subject, type):
        return subject.__name__
    return type(subject).__name__


def _is_instance(subject: object) -> bool:
    return not isinstance(subject, str | type)


_OPS: dict[str, Any] = {
    "$eq": lambda a, b: a == b,
    "$ne": lambda a, b: a != b,
    "$in": lambda a, b: a in b,
    "$nin": lambda a, b: a not in b,
    "$gt": lambda a, b: a > b,
    "$gte": lambda a, b: a >= b,
    "$lt": lambda a, b: a < b,
    "$lte": lambda a, b: a <= b,
}


def _matches_value(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping):
        return all(_OPS[op](actual, arg) for op, arg in expected.items())
    return bool(actual == expected)


def matches(obj: object, conditions: Mapping[str, Any]) -> bool:
    return all(_matches_value(getattr(obj, f), exp) for f, exp in conditions.items())


def _sql_condition(model: Any, conditions: Mapping[str, Any]) -> ColumnElement[bool]:
    ops: dict[str, Any] = {
        "$eq": lambda c, v: c == v,
        "$ne": lambda c, v: c != v,
        "$in": lambda c, v: c.in_(v),
        "$nin": lambda c, v: c.not_in(v),
        "$gt": lambda c, v: c > v,
        "$gte": lambda c, v: c >= v,
        "$lt": lambda c, v: c < v,
        "$lte": lambda c, v: c <= v,
    }
    clauses: list[ColumnElement[bool]] = []
    for field_name, expected in conditions.items():
        column = getattr(model, field_name)
        if isinstance(expected, Mapping):
            clauses.extend(ops[op](column, arg) for op, arg in expected.items())
        else:
            clauses.append(column == expected)
    return and_(true(), *clauses)


class Ability:
    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self.rules: tuple[Rule, ...] = tuple(rules)

    def relevant_rules(self, action: str, subject_type: str) -> list[Rule]:
        return [
            r
            for r in self.rules
            if r.action in (action, Action.MANAGE) and r.subject in (subject_type, ALL)
        ]

    def can(self, action: str, subject: object, field: str | None = None) -> bool:
        instance = _is_instance(subject)
        for rule in reversed(self.relevant_rules(action, subject_name(subject))):
            if rule.inverted and not instance and rule.conditions:
                continue  # a conditional "cannot" cannot deny a whole class
            if field is None:
                if rule.inverted and rule.fields:
                    continue  # a field-level "cannot" cannot deny the whole subject
            elif rule.fields and field not in rule.fields:
                continue
            if instance and rule.conditions and not matches(subject, rule.conditions):
                continue
            return not rule.inverted
        return False

    def cannot(self, action: str, subject: object, field: str | None = None) -> bool:
        return not self.can(action, subject, field)

    def authorize(self, action: str, subject: object, field: str | None = None) -> None:
        """Raise ForbiddenError unless allowed (CASL's `ForbiddenError.throwUnlessCan`)."""
        if not self.can(action, subject, field):
            raise ForbiddenError(action, subject_name(subject), field)


def accessible_by(ability: Ability, action: str, model: type) -> ColumnElement[bool]:
    """SQL WHERE clause selecting the rows of `model` the ability allows for `action`."""
    clause: ColumnElement[bool] = false()
    for rule in ability.relevant_rules(action, model.__name__):
        cond = _sql_condition(model, rule.conditions) if rule.conditions else true()
        if rule.inverted:
            if rule.fields:
                continue
            clause = and_(clause, not_(cond))
        else:
            clause = or_(clause, cond)
    return clause


def _as_list(value: Any) -> list[Any]:
    return [value] if isinstance(value, str | type) else list(value)


class AbilityBuilder:
    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def _add(
        self,
        actions: Any,
        subjects: Any,
        conditions: Mapping[str, Any] | None,
        fields: Iterable[str] | None,
        inverted: bool,
    ) -> "AbilityBuilder":
        for action in _as_list(actions):
            for subject in _as_list(subjects):
                self._rules.append(
                    Rule(
                        str(action),
                        subject_name(subject),
                        conditions,
                        tuple(fields) if fields else None,
                        inverted,
                    )
                )
        return self

    def can(
        self,
        actions: Any,
        subjects: Any,
        conditions: Mapping[str, Any] | None = None,
        fields: Iterable[str] | None = None,
    ) -> "AbilityBuilder":
        return self._add(actions, subjects, conditions, fields, inverted=False)

    def cannot(
        self,
        actions: Any,
        subjects: Any,
        conditions: Mapping[str, Any] | None = None,
        fields: Iterable[str] | None = None,
    ) -> "AbilityBuilder":
        return self._add(actions, subjects, conditions, fields, inverted=True)

    def build(self) -> Ability:
        return Ability(self._rules)
