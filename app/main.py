from contextlib import asynccontextmanager

from celery.result import AsyncResult
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from sqlmodel import Session

from app import crud
from app.celery_app import celery_app
from app.database import DEFAULT, get_session, init_db, known_databases
from app.models import TodoCreate, TodoRead, TodoUpdate
from app.tasks import notify_todo_created, purge_completed_todos


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Todo API", lifespan=lifespan)


def _todo_or_404(session: Session, todo_id: int):
    todo = crud.get_todo(session, todo_id)
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")
    return todo


@app.get("/databases")
def list_databases():
    return sorted(known_databases())


@app.post("/todos", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(
    data: TodoCreate,
    session: Session = Depends(get_session),
    x_database: str | None = Header(default=None),
):
    todo = crud.create_todo(session, data)
    notify_todo_created.delay(todo.id, x_database or DEFAULT)
    return todo


@app.get("/todos", response_model=list[TodoRead])
def list_todos(
    completed: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    return crud.list_todos(session, completed, offset, limit)


@app.get("/todos/{todo_id}", response_model=TodoRead)
def read_todo(todo_id: int, session: Session = Depends(get_session)):
    return _todo_or_404(session, todo_id)


@app.patch("/todos/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, data: TodoUpdate, session: Session = Depends(get_session)):
    return crud.update_todo(session, _todo_or_404(session, todo_id), data)


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    crud.delete_todo(session, _todo_or_404(session, todo_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/tasks/purge-completed", status_code=status.HTTP_202_ACCEPTED)
def trigger_purge(
    older_than_days: int = Query(30, ge=0), x_database: str | None = Header(default=None)
):
    name = x_database or DEFAULT
    if name not in known_databases():
        raise HTTPException(400, f"Unknown database '{name}'")
    result = purge_completed_todos.delay(older_than_days, name)
    return {"task_id": result.id}


@app.get("/tasks/{task_id}")
def task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
