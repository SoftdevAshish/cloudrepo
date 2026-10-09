from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.casl import Ability
from app.core.database import get_db_name, get_session
from app.features.auth.dependencies import get_ability, get_current_user
from app.features.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.features.auth.service import AuthService, InvalidCredentialsError
from app.features.users.models import User
from app.features.users.repository import UsersRepository
from app.features.users.schemas import UserRead
from app.features.users.service import EmailTakenError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: Session = Depends(get_session), db_name: str = Depends(get_db_name)
) -> AuthService:
    return AuthService(UsersRepository(session), db_name)


def _invalid() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> User:
    try:
        return service.register(data)
    except EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        return service.login(data)
    except InvalidCredentialsError:
        raise _invalid() from None


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        return service.refresh(data.refresh_token)
    except InvalidCredentialsError:
        raise _invalid() from None


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/me/abilities")
def my_abilities(ability: Ability = Depends(get_ability)) -> list[dict[str, Any]]:
    """The caller's effective rules (placeholders resolved), e.g. to drive a UI with CASL."""
    return [
        {
            "action": r.action,
            "subject": r.subject,
            "conditions": dict(r.conditions) if r.conditions else None,
            "fields": list(r.fields) if r.fields else None,
            "inverted": r.inverted,
        }
        for r in ability.rules
    ]
