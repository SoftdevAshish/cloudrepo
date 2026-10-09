from fastapi import APIRouter

from app.api.v1 import system
from app.features.auth.controller import router as auth_router
from app.features.roles.controller import policies_router
from app.features.roles.controller import router as roles_router
from app.features.todos.controller import router as todos_router
from app.features.users.controller import router as users_router

api_router = APIRouter(prefix="/api/v1")
for router in (
    system.router,
    auth_router,
    users_router,
    roles_router,
    policies_router,
    todos_router,
):
    api_router.include_router(router)
