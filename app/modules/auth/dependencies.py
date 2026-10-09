from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.casl import Ability, ForbiddenError
from app.core.database import get_db_name, get_session
from app.core.security import ACCESS, TokenError, decode_token
from app.modules.auth.abilities import define_abilities
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository

bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
    db_name: str = Depends(get_db_name),
) -> User:
    """Authentication guard (cf. Nest's JwtAuthGuard): resolves the user from the bearer token."""
    if credentials is None:
        raise _unauthorized()
    try:
        user_id = decode_token(credentials.credentials, ACCESS, db_name)
    except TokenError:
        raise _unauthorized("Invalid or expired token") from None
    user = UsersRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    return user


def get_ability(user: User = Depends(get_current_user)) -> Ability:
    return define_abilities(user)


def check_policies(action: str, subject: object) -> Callable[..., None]:
    """Policies guard (cf. Nest's PoliciesGuard + @CheckPolicies): coarse, class-level check.

    Instance-level checks happen in services via `ability.authorize(action, instance)`.
    """

    def guard(ability: Ability = Depends(get_ability)) -> None:
        ability.authorize(action, subject)

    return guard


__all__ = ["ForbiddenError", "check_policies", "get_ability", "get_current_user"]
