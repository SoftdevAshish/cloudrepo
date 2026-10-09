from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class RegisterRequest(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt ignores bytes past 72


class LoginRequest(SQLModel):
    email: EmailStr
    password: str = Field(max_length=72)


class RefreshRequest(SQLModel):
    refresh_token: str


class TokenPair(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
