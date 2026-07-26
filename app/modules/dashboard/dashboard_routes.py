from fastapi import APIRouter, Depends

from app.dependencies.authentication import auth_guard

from .dashboard_schema import DashboardHomeResponse
from .dashboard_service import DashboardService, get_dashboard_service

dashboard_router = APIRouter(dependencies=[Depends(auth_guard)])


@dashboard_router.get("/home", response_model=DashboardHomeResponse)
async def get_home(service: DashboardService = Depends(get_dashboard_service)):
    return await service.get_home()
