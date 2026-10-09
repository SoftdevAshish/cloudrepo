from sqlmodel import Session, col, select

from app.models import Todo, TodoCreate, TodoUpdate, utcnow


def create_todo(session: Session, data: TodoCreate) -> Todo:
    todo = Todo.model_validate(data)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def list_todos(
    session: Session, completed: bool | None = None, offset: int = 0, limit: int = 100
) -> list[Todo]:
    stmt = select(Todo).order_by(col(Todo.id)).offset(offset).limit(limit)
    if completed is not None:
        stmt = stmt.where(Todo.completed == completed)
    return list(session.exec(stmt))


def get_todo(session: Session, todo_id: int) -> Todo | None:
    return session.get(Todo, todo_id)


def update_todo(session: Session, todo: Todo, data: TodoUpdate) -> Todo:
    todo.sqlmodel_update(data.model_dump(exclude_unset=True))
    todo.updated_at = utcnow()
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def delete_todo(session: Session, todo: Todo) -> None:
    session.delete(todo)
    session.commit()
