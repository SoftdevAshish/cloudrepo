import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.casl import ForbiddenError
from app.core.database import DEFAULT, init_db, session_for
from app.modules.auth.controller import router as auth_router
from app.modules.auth.service import ensure_admin
from app.modules.roles.controller import policies_router
from app.modules.roles.controller import router as roles_router
from app.modules.system.controller import router as system_router
from app.modules.todos.controller import router as todos_router
from app.modules.users.controller import router as users_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    with session_for(DEFAULT) as session:
        ensure_admin(session)
    yield


app = FastAPI(title="Todo API", version="0.4.0", lifespan=lifespan)


@app.exception_handler(ForbiddenError)
async def forbidden_handler(_: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


for router in (
    system_router,
    auth_router,
    users_router,
    roles_router,
    policies_router,
    todos_router,
):
    app.include_router(router)
