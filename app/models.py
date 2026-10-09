from datetime import UTC, datetime

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=200, index=True)
    description: str | None = None
    completed: bool = False


class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: NaiveDatetime = Field(default_factory=utcnow)
    updated_at: NaiveDatetime = Field(default_factory=utcnow)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoRead(TodoBase):
    id: int
    created_at: NaiveDatetime
    updated_at: NaiveDatetime
