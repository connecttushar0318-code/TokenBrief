from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from database import get_database_session
from models import UserAccount
from security import get_optional_authenticated_user
from schemas import AnalyticsDashboardResponse
from services.analytics_service import AnalyticsDashboardService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard_metrics(
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    user_id = optional_user_account.id if optional_user_account else None
    dashboard_data = await AnalyticsDashboardService.get_dashboard_metrics(
        database_session=database_session,
        user_id=user_id
    )
    return dashboard_data
