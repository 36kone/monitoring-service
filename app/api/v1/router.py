from fastapi import APIRouter

from app.modules.auth.auth_routes import auth_router
from app.modules.monitor.monitor_routes import monitor_router
from app.modules.user.user_routes import user_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(monitor_router, prefix="/monitors", tags=["monitors"])
