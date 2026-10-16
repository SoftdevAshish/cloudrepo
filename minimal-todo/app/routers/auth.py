from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.config import get_settings
from app.deps import CurrentUser, SessionDep
from app.models import User
from app.schemas import Credentials, Token, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash used to keep login timing similar when the email does not exist.
_DUMMY_HASH = hash_password("not-a-real-password")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: Credentials, session: SessionDep) -> User:
    email = data.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    role = "admin" if email in get_settings().admin_email_set else "user"
    user = User(email=email, password_hash=hash_password(data.password), role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: Credentials, session: SessionDep) -> Token:
    user = session.exec(select(User).where(User.email == data.email.lower())).first()
    ok = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return Token(access_token=create_access_token(user.id))  # type: ignore[arg-type]


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
