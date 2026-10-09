from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.core.casl import Ability, Action
from app.core.database import get_session
from app.modules.auth.dependencies import check_policies, get_ability
from app.modules.roles.repository import RolesRepository
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.service import (
    EmailTakenError,
    InvalidRoleError,
    UserNotFoundError,
    UsersService,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_users_service(
    session: Session = Depends(get_session), ability: Ability = Depends(get_ability)
) -> UsersService:
    return UsersService(UsersRepository(session), ability, RolesRepository(session))


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "User not found")


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(check_policies(Action.READ, User))],
)
def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: UsersService = Depends(get_users_service),
) -> list[User]:
    return service.list(offset, limit)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, service: UsersService = Depends(get_users_service)) -> User:
    try:
        return service.get(user_id)
    except UserNotFoundError:
        raise _not_found() from None


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, data: UserUpdate, service: UsersService = Depends(get_users_service)
) -> User:
    try:
        return service.update(user_id, data)
    except UserNotFoundError:
        raise _not_found() from None
    except EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None
    except InvalidRoleError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown role") from None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, service: UsersService = Depends(get_users_service)) -> Response:
    try:
        service.delete(user_id)
    except UserNotFoundError:
        raise _not_found() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
