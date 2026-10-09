from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt

from app.core.config import settings

ACCESS = "access"
REFRESH = "refresh"


class TokenError(Exception):
    """The token is missing, malformed, expired or not valid for this request."""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(settings.bcrypt_rounds)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


@lru_cache
def dummy_hash() -> str:
    """Verified against when a user is unknown so login timing does not reveal valid emails."""
    return hash_password("not-a-real-password")


def create_token(user_id: int, db: str, token_type: str, expires_in: timedelta) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "type": token_type,
        "db": db,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, token_type: str, db: str) -> int:
    """Validate signature, expiry, type and database binding; return the user id."""
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
        if claims.get("type") != token_type or claims.get("db") != db:
            raise TokenError("wrong token type or database")
        return int(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise TokenError(str(exc)) from exc
