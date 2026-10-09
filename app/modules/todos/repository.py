from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, select

from app.modules.todos.models import Todo


class TodosRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, todo_id: int) -> Todo | None:
        return self.session.get(Todo, todo_id)

    def list(
        self, where: ColumnElement[bool], completed: bool | None, offset: int, limit: int
    ) -> list[Todo]:
        stmt = select(Todo).where(where).order_by(col(Todo.id)).offset(offset).limit(limit)
        if completed is not None:
            stmt = stmt.where(Todo.completed == completed)
        return list(self.session.exec(stmt))

    def save(self, todo: Todo) -> Todo:
        self.session.add(todo)
        self.session.commit()
        self.session.refresh(todo)
        return todo

    def delete(self, todo: Todo) -> None:
        self.session.delete(todo)
        self.session.commit()
