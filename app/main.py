import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health
from app.api.v1.router import api_router
from app.core.casl import ForbiddenError
from app.core.database import DEFAULT, init_db, session_for
from app.features.auth.service import ensure_admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    with session_for(DEFAULT) as session:
        ensure_admin(session)
    yield


app = FastAPI(title="Todo API", version="0.5.0", lifespan=lifespan)


@app.exception_handler(ForbiddenError)
async def forbidden_handler(_: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(api_router)
