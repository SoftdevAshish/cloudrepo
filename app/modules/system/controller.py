import logging
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, text

from app.celery_app import celery_app
from app.core.casl import Action
from app.core.database import get_db_name, get_session, known_databases
from app.modules.auth.abilities import SYSTEM
from app.modules.auth.dependencies import check_policies
from app.modules.todos.tasks import purge_completed_todos

logger = logging.getLogger(__name__)

router = APIRouter()
admin_only = [Depends(check_policies(Action.MANAGE, SYSTEM))]


@router.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@router.get("/ready", tags=["ops"])
def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    """Readiness: the database answers."""
    try:
        session.exec(text("SELECT 1"))  # type: ignore[call-overload]
    except Exception as exc:
        logger.exception("readiness check failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable") from exc
    return {"status": "ready"}


@router.get("/databases", tags=["ops"], dependencies=admin_only)
def list_databases() -> list[str]:
    return sorted(known_databases())


@router.post(
    "/tasks/purge-completed",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"],
    dependencies=admin_only,
)
def trigger_purge(
    older_than_days: int = Query(30, ge=0), db_name: str = Depends(get_db_name)
) -> dict[str, str]:
    result = purge_completed_todos.delay(older_than_days, db_name)
    return {"task_id": result.id}


@router.get("/tasks/{task_id}", tags=["tasks"], dependencies=admin_only)
def task_status(task_id: str) -> dict[str, Any]:
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
