"""Password hashing (bcrypt) and signed access tokens (JWT)."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: int) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=s.access_token_minutes),
    }
    return jwt.encode(payload, s.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id, or None if the token is invalid or expired."""
    try:
        data = jwt.decode(
            token,
            get_settings().secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(data["sub"])
    except (jwt.PyJWTError, ValueError):
        return None
