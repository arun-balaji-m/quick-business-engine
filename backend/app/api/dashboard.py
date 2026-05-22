from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.schemas.dashboard import DashboardMetrics, DashboardChartData
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get KPI metrics for the current user's dashboard."""
    svc = DashboardService(db)
    return await svc.get_metrics(current_user.id)


@router.get("/charts", response_model=DashboardChartData)
async def get_chart_data(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get chart data for the dashboard (healthcare & business metrics)."""
    svc = DashboardService(db)
    return await svc.get_chart_data()
