from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "todo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.features.todos.tasks"],
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    beat_schedule={
        "purge-completed-todos-daily": {
            "task": "todos.purge_completed",
            "schedule": crontab(hour=3, minute=0),
            "args": (30,),
        },
    },
)
