from pydantic import EmailStr, NaiveDatetime
from sqlmodel import Field, SQLModel

from app.modules.users.models import Role


class UserRead(SQLModel):
    id: int
    email: str
    role: Role
    is_active: bool
    created_at: NaiveDatetime


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Role | None = None
    is_active: bool | None = None
