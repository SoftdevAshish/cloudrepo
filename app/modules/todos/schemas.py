from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


class TodoCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    completed: bool = False


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoRead(SQLModel):
    id: int
    title: str
    description: str | None
    completed: bool
    owner_id: int
    created_at: NaiveDatetime
    updated_at: NaiveDatetime
