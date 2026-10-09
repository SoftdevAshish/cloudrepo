from pydantic import EmailStr, Field, NaiveDatetime
from sqlmodel import SQLModel


class UserRead(SQLModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: NaiveDatetime


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_-]{1,31}$")
    is_active: bool | None = None
