from pydantic import NaiveDatetime
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.features.users.models import utcnow

ADMIN_ROLE = "admin"  # always has `manage all`; its policies are immutable
USER_ROLE = "user"  # default role for self-registered users


class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=32)
    description: str | None = None
    is_system: bool = False  # system roles cannot be deleted
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class Policy(SQLModel, table=True):
    """One CASL rule belonging to a role. Later policies (higher id) override earlier ones."""

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="role.id", index=True)
    action: str = Field(max_length=16)
    subject: str = Field(max_length=32)
    conditions: dict | None = Field(default=None, sa_column=Column(JSON))  # type: ignore[type-arg]
    fields: list | None = Field(default=None, sa_column=Column(JSON))  # type: ignore[type-arg]
    inverted: bool = False
