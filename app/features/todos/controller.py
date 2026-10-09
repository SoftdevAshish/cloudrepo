from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.core.casl import Ability, Action
from app.core.database import get_db_name, get_session
from app.features.auth.dependencies import check_policies, get_ability, get_current_user
from app.features.todos.models import Todo
from app.features.todos.repository import TodosRepository
from app.features.todos.schemas import TodoCreate, TodoRead, TodoUpdate
from app.features.todos.service import TodoNotFoundError, TodosService
from app.features.users.models import User

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todos_service(
    session: Session = Depends(get_session),
    ability: Ability = Depends(get_ability),
    user: User = Depends(get_current_user),
    db_name: str = Depends(get_db_name),
) -> TodosService:
    return TodosService(TodosRepository(session), ability, user, db_name)


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")


@router.post(
    "",
    response_model=TodoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_policies(Action.CREATE, Todo))],
)
def create_todo(data: TodoCreate, service: TodosService = Depends(get_todos_service)) -> Todo:
    return service.create(data)


@router.get(
    "",
    response_model=list[TodoRead],
    dependencies=[Depends(check_policies(Action.READ, Todo))],
)
def list_todos(
    completed: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: TodosService = Depends(get_todos_service),
) -> list[Todo]:
    return service.list(completed, offset, limit)


@router.get("/{todo_id}", response_model=TodoRead)
def read_todo(todo_id: int, service: TodosService = Depends(get_todos_service)) -> Todo:
    try:
        return service.get(todo_id)
    except TodoNotFoundError:
        raise _not_found() from None


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo(
    todo_id: int, data: TodoUpdate, service: TodosService = Depends(get_todos_service)
) -> Todo:
    try:
        return service.update(todo_id, data)
    except TodoNotFoundError:
        raise _not_found() from None


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, service: TodosService = Depends(get_todos_service)) -> Response:
    try:
        service.delete(todo_id)
    except TodoNotFoundError:
        raise _not_found() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
