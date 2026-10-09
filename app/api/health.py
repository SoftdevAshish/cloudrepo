"""Unversioned probes used by Kubernetes / load balancers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, text

from app.core.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ops"])


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
