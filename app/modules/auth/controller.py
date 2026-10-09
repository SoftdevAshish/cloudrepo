from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_db_name, get_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.modules.auth.service import AuthService, InvalidCredentialsError
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository
from app.modules.users.schemas import UserRead
from app.modules.users.service import EmailTakenError

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
