from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db import get_session
from app.models import User
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    """Authentication: turn the Bearer token into a User or answer 401."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Invalid or missing token", {"WWW-Authenticate": "Bearer"}
    )
    if creds is None:
        raise unauthorized
    user_id = decode_access_token(creds.credentials)
    user = session.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
