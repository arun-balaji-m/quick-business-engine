from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.queries import router as queries_router
from app.api.tickets import router as tickets_router
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(queries_router)
api_router.include_router(tickets_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
