from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, delete, select

from app.features.users.models import User


class UsersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email.lower())).first()

    def list(self, where: ColumnElement[bool], offset: int, limit: int) -> list[User]:
        stmt = select(User).where(where).order_by(col(User.id)).offset(offset).limit(limit)
        return list(self.session.exec(stmt))

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> None:
        from app.features.todos.models import Todo  # noqa: PLC0415

        self.session.exec(delete(Todo).where(col(Todo.owner_id) == user.id))
        self.session.delete(user)
        self.session.commit()
