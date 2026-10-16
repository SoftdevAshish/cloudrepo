from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import auth, todos


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()  # dev convenience; production would use migrations (see docs/design.md)
    yield


app = FastAPI(title="Minimal Todo API", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}
