"""API routes for Schedules and WBS"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_schedule.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    WBSCreate, WBSUpdate, WBSResponse,
)
from addons.agcm_schedule.services.schedule_service import ScheduleService

router = APIRouter()


def _get_service(db: Session, current_user) -> ScheduleService:
    company_id = get_effective_company_id(current_user, db)
    return ScheduleService(db=db, company_id=company_id, user_id=current_user.id)


# =============================================================================
# SCHEDULES
# =============================================================================

@router.get("/schedules", response_model=None)
async def list_schedules(
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List schedule versions for a project."""
    svc = _get_service(db, current_user)
    items = svc.list_schedules(project_id)
    return {
        "items": [ScheduleResponse.model_validate(s).model_dump() for s in items],
        "total": len(items),
    }


@router.post("/schedules", response_model=None, status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new schedule version."""
    svc = _get_service(db, current_user)
    schedule = svc.create_schedule(data)
    return ScheduleResponse.model_validate(schedule).model_dump()


@router.put("/schedules/{schedule_id}", response_model=None)
async def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a schedule."""
    svc = _get_service(db, current_user)
    schedule = svc.update_schedule(schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate(schedule).model_dump()


@router.post("/schedules/{schedule_id}/activate", response_model=None)
async def activate_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Activate a schedule (deactivates others for the same project)."""
    svc = _get_service(db, current_user)
    schedule = svc.activate_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate(schedule).model_dump()


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a schedule and all related data."""
    svc = _get_service(db, current_user)
    if not svc.delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")


# =============================================================================
# WBS
# =============================================================================

@router.get("/wbs", response_model=None)
async def list_wbs(
    schedule_id: int = Query(..., description="Schedule ID"),
    tree: Optional[bool] = Query(False, description="Return as tree structure"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List WBS items for a schedule."""
    svc = _get_service(db, current_user)
    if tree:
        return {"items": svc.get_wbs_tree(schedule_id)}
    items = svc.list_wbs(schedule_id)
    return {
        "items": [WBSResponse.model_validate(w).model_dump() for w in items],
        "total": len(items),
    }


@router.post("/wbs", response_model=None, status_code=201)
async def create_wbs(
    data: WBSCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a WBS item."""
    svc = _get_service(db, current_user)
    wbs = svc.create_wbs(data)
    return WBSResponse.model_validate(wbs).model_dump()


@router.put("/wbs/{wbs_id}", response_model=None)
async def update_wbs(
    wbs_id: int,
    data: WBSUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a WBS item."""
    svc = _get_service(db, current_user)
    wbs = svc.update_wbs(wbs_id, data)
    if not wbs:
        raise HTTPException(status_code=404, detail="WBS item not found")
    return WBSResponse.model_validate(wbs).model_dump()


@router.delete("/wbs/{wbs_id}", status_code=204)
async def delete_wbs(
    wbs_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a WBS item."""
    svc = _get_service(db, current_user)
    if not svc.delete_wbs(wbs_id):
        raise HTTPException(status_code=404, detail="WBS item not found")
