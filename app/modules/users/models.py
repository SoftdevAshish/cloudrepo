from datetime import UTC, datetime
from enum import StrEnum

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=254)
    hashed_password: str
    role: str = Field(default=Role.USER.value)
    is_active: bool = True
    created_at: NaiveDatetime = Field(default_factory=utcnow)
