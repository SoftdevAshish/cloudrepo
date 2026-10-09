from app.core.casl import Ability, Action, accessible_by
from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UsersRepository
from app.modules.users.schemas import UserUpdate


class UserNotFoundError(Exception):
    pass


class EmailTakenError(Exception):
    pass


class UsersService:
    def __init__(self, repo: UsersRepository, ability: Ability) -> None:
        self.repo = repo
        self.ability = ability

    def list(self, offset: int, limit: int) -> list[User]:
        where = accessible_by(self.ability, Action.READ, User)
        return self.repo.list(where, offset, limit)

    def get(self, user_id: int, action: Action = Action.READ) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        self.ability.authorize(action, user)
        return user

    def update(self, user_id: int, data: UserUpdate) -> User:
        user = self.get(user_id, Action.UPDATE)
        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        for field_name in changes:  # field-level rules, e.g. only admins may change `role`
            self.ability.authorize(Action.UPDATE, user, field_name)
        if "email" in changes:
            email = str(changes["email"]).lower()
            other = self.repo.get_by_email(email)
            if other is not None and other.id != user.id:
                raise EmailTakenError(email)
            user.email = email
        if "password" in changes:
            user.hashed_password = hash_password(changes["password"])
        if "role" in changes:
            user.role = changes["role"].value
        if "is_active" in changes:
            user.is_active = changes["is_active"]
        return self.repo.add(user)

    def delete(self, user_id: int) -> None:
        self.repo.delete(self.get(user_id, Action.DELETE))
