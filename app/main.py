import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from celery.result import AsyncResult
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from sqlmodel import Session, text

from app import crud
from app.celery_app import celery_app
from app.database import DEFAULT, get_session, init_db, known_databases
from app.models import Todo, TodoCreate, TodoRead, TodoUpdate
from app.tasks import notify_todo_created, purge_completed_todos

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Todo API", version="0.2.0", lifespan=lifespan)


def _todo_or_404(session: Session, todo_id: int) -> Todo:
    todo = crud.get_todo(session, todo_id)
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")
    return todo


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    """Readiness: the database answers."""
    try:
        session.exec(text("SELECT 1"))  # type: ignore[call-overload]
    except Exception as exc:
        logger.exception("readiness check failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable") from exc
    return {"status": "ready"}


@app.get("/databases", tags=["ops"])
def list_databases() -> list[str]:
    return sorted(known_databases())


@app.post("/todos", response_model=TodoRead, status_code=status.HTTP_201_CREATED, tags=["todos"])
def create_todo(
    data: TodoCreate,
    session: Session = Depends(get_session),
    x_database: str | None = Header(default=None),
) -> Todo:
    todo = crud.create_todo(session, data)
    assert todo.id is not None  # noqa: S101 - set by the DB after commit
    notify_todo_created.delay(todo.id, x_database or DEFAULT)
    return todo


@app.get("/todos", response_model=list[TodoRead], tags=["todos"])
def list_todos(
    completed: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[Todo]:
    return crud.list_todos(session, completed, offset, limit)


@app.get("/todos/{todo_id}", response_model=TodoRead, tags=["todos"])
def read_todo(todo_id: int, session: Session = Depends(get_session)) -> Todo:
    return _todo_or_404(session, todo_id)


@app.patch("/todos/{todo_id}", response_model=TodoRead, tags=["todos"])
def update_todo(todo_id: int, data: TodoUpdate, session: Session = Depends(get_session)) -> Todo:
    return crud.update_todo(session, _todo_or_404(session, todo_id), data)


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["todos"])
def delete_todo(todo_id: int, session: Session = Depends(get_session)) -> Response:
    crud.delete_todo(session, _todo_or_404(session, todo_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/tasks/purge-completed", status_code=status.HTTP_202_ACCEPTED, tags=["tasks"])
def trigger_purge(
    older_than_days: int = Query(30, ge=0), x_database: str | None = Header(default=None)
) -> dict[str, str]:
    name = x_database or DEFAULT
    if name not in known_databases():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown database '{name}'")
    result = purge_completed_todos.delay(older_than_days, name)
    return {"task_id": result.id}


@app.get("/tasks/{task_id}", tags=["tasks"])
def task_status(task_id: str) -> dict[str, Any]:
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
