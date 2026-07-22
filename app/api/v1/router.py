from fastapi import APIRouter

from app.modules.auth.auth_routes import auth_router
from app.modules.incident.incident_routes import incident_router
from app.modules.monitor.monitor_routes import monitor_router
from app.modules.monitor_check.monitor_check_routes import monitor_check_router
from app.modules.user.user_routes import user_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(monitor_router, prefix="/monitors", tags=["Monitors"])
api_router.include_router(monitor_check_router, prefix="/monitor-checks", tags=["Monitor Checks"])
api_router.include_router(incident_router, prefix="/incidents", tags=["Incidents"])
