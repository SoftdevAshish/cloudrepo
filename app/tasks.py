import logging
from datetime import timedelta
from typing import Any

from sqlmodel import col, delete

from app import database
from app.celery_app import celery_app
from app.models import Todo, utcnow

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.notify_todo_created")
def notify_todo_created(todo_id: int, db: str = database.DEFAULT) -> dict[str, Any]:
    """Background hook run after a todo is created (stand-in for email/push)."""
    with database.session_for(db) as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return {"todo_id": todo_id, "status": "missing"}
        logger.info("Todo created: #%s %s", todo.id, todo.title)
        return {"todo_id": todo.id, "status": "notified", "title": todo.title}


@celery_app.task(name="app.tasks.purge_completed_todos")
def purge_completed_todos(older_than_days: int = 30, db: str = database.DEFAULT) -> int:
    """Delete completed todos not updated for `older_than_days` days in database `db`."""
    cutoff = utcnow() - timedelta(days=older_than_days)
    with database.session_for(db) as session:
        result = session.exec(
            delete(Todo).where(col(Todo.completed).is_(True), col(Todo.updated_at) < cutoff)
        )
        session.commit()
        return result.rowcount
