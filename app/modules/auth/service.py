from datetime import timedelta

from sqlmodel import Session

from app.core.config import settings
from app.core.security import (
    ACCESS,
    REFRESH,
    TokenError,
    create_token,
    decode_token,
    dummy_hash,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenPair
from app.modules.users.models import Role, User
from app.modules.users.repository import UsersRepository
from app.modules.users.service import EmailTakenError


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, users: UsersRepository, db_name: str) -> None:
        self.users = users
        self.db_name = db_name

    def register(self, data: RegisterRequest) -> User:
        email = str(data.email).lower()
        if self.users.get_by_email(email) is not None:
            raise EmailTakenError(email)
        user = User(email=email, hashed_password=hash_password(data.password), role=Role.USER)
        return self.users.add(user)

    def _tokens(self, user: User) -> TokenPair:
        assert user.id is not None  # noqa: S101
        return TokenPair(
            access_token=create_token(
                user.id,
                self.db_name,
                ACCESS,
                timedelta(minutes=settings.access_token_expire_minutes),
            ),
            refresh_token=create_token(
                user.id,
                self.db_name,
                REFRESH,
                timedelta(days=settings.refresh_token_expire_days),
            ),
        )

    def login(self, data: LoginRequest) -> TokenPair:
        user = self.users.get_by_email(str(data.email))
        # Always run one bcrypt check so response time does not reveal whether the email exists.
        valid = verify_password(data.password, user.hashed_password if user else dummy_hash())
        if user is None or not valid or not user.is_active:
            raise InvalidCredentialsError
        return self._tokens(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            user_id = decode_token(refresh_token, REFRESH, self.db_name)
        except TokenError as exc:
            raise InvalidCredentialsError from exc
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError
        return self._tokens(user)


def ensure_admin(session: Session) -> None:
    """Create the configured first administrator if it does not exist yet."""
    if not (settings.admin_email and settings.admin_password):
        return
    repo = UsersRepository(session)
    email = settings.admin_email.lower()
    if repo.get_by_email(email) is None:
        repo.add(
            User(
                email=email,
                hashed_password=hash_password(settings.admin_password),
                role=Role.ADMIN,
            )
        )
