from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from app.deps import CurrentUser, SessionDep
from app.models import Todo, utcnow
from app.policies import Action, authorize, scope
from app.schemas import TodoCreate, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


def _get_or_404(session: SessionDep, todo_id: int) -> Todo:
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")
    return todo


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoCreate, user: CurrentUser, session: SessionDep) -> Todo:
    authorize(user, Action.CREATE)
    todo = Todo(**data.model_dump(), owner_id=user.id)  # type: ignore[arg-type]
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@router.get("", response_model=list[TodoOut])
def list_todos(
    user: CurrentUser,
    session: SessionDep,
    done: bool | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Todo]:
    stmt = scope(user, Action.READ, select(Todo))  # only rows the policy allows
    if done is not None:
        stmt = stmt.where(Todo.done == done)
    stmt = stmt.order_by(Todo.id).offset(skip).limit(limit)  # type: ignore[arg-type]
    return list(session.exec(stmt).all())


@router.get("/{todo_id}", response_model=TodoOut)
def read_todo(todo_id: int, user: CurrentUser, session: SessionDep) -> Todo:
    todo = _get_or_404(session, todo_id)
    authorize(user, Action.READ, todo)
    return todo


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, data: TodoUpdate, user: CurrentUser, session: SessionDep) -> Todo:
    todo = _get_or_404(session, todo_id)
    authorize(user, Action.UPDATE, todo)
    todo.sqlmodel_update(data.model_dump(exclude_unset=True))
    todo.updated_at = utcnow()
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, user: CurrentUser, session: SessionDep) -> None:
    todo = _get_or_404(session, todo_id)
    authorize(user, Action.DELETE, todo)
    session.delete(todo)
    session.commit()
