"""API routes for Gantt chart data"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_schedule.schemas.schedule import (
    TaskResponse, DependencyResponse, WBSResponse,
)
from addons.agcm_schedule.services.schedule_service import ScheduleService

router = APIRouter()


def _get_service(db: Session, current_user) -> ScheduleService:
    company_id = get_effective_company_id(current_user, db)
    return ScheduleService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/gantt", response_model=None)
async def get_gantt_data(
    project_id: int = Query(..., description="Project ID"),
    schedule_id: int = Query(..., description="Schedule ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all data needed for Gantt chart rendering."""
    svc = _get_service(db, current_user)
    data = svc.get_gantt_data(project_id, schedule_id)
    return {
        "tasks": [TaskResponse.model_validate(t).model_dump() for t in data["tasks"]],
        "dependencies": [DependencyResponse.model_validate(d).model_dump() for d in data["dependencies"]],
        "wbs_items": [WBSResponse.model_validate(w).model_dump() for w in data["wbs_items"]],
    }
