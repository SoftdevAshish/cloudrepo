from typing import Any

from pydantic import Field, NaiveDatetime, model_validator
from sqlmodel import SQLModel

from app.features.roles.registry import validate_rule

NAME_PATTERN = r"^[a-z][a-z0-9_-]{1,31}$"


class RoleCreate(SQLModel):
    name: str = Field(pattern=NAME_PATTERN)
    description: str | None = Field(default=None, max_length=200)


class RoleUpdate(SQLModel):
    description: str | None = Field(default=None, max_length=200)


class RoleRead(SQLModel):
    id: int
    name: str
    description: str | None
    is_system: bool
    created_at: NaiveDatetime


class PolicyIn(SQLModel):
    """A CASL rule. Example: allow managing todos you own."""

    action: str = Field(examples=["manage"])
    subject: str = Field(examples=["Todo"])
    conditions: dict[str, Any] | None = Field(default=None, examples=[{"owner_id": "${user.id}"}])
    fields: list[str] | None = None
    inverted: bool = Field(default=False, description="true = 'cannot' rule")

    @model_validator(mode="after")
    def _validate(self) -> "PolicyIn":
        validate_rule(self.action, self.subject, self.conditions, self.fields)
        return self


class PolicyRead(SQLModel):
    id: int
    role_id: int
    action: str
    subject: str
    conditions: dict[str, Any] | None
    fields: list[str] | None
    inverted: bool
