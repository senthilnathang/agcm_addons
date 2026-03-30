"""API routes for Milestones"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_progress.schemas.progress import (
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
)
from addons.agcm_progress.services.progress_service import ProgressService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProgressService:
    company_id = get_effective_company_id(current_user, db)
    return ProgressService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/milestones", response_model=None)
async def list_milestones(
    project_id: int = Query(..., description="Filter by project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List milestones for a project."""
    svc = _get_service(db, current_user)
    items = svc.list_milestones(project_id)
    return {"items": items, "total": len(items)}


@router.post("/milestones", response_model=None, status_code=201)
async def create_milestone(
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new milestone."""
    svc = _get_service(db, current_user)
    milestone = svc.create_milestone(data)
    return MilestoneResponse.model_validate(milestone).model_dump()


@router.put("/milestones/{milestone_id}", response_model=None)
async def update_milestone(
    milestone_id: int,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a milestone."""
    svc = _get_service(db, current_user)
    milestone = svc.update_milestone(milestone_id, data)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return MilestoneResponse.model_validate(milestone).model_dump()


@router.delete("/milestones/{milestone_id}", status_code=204)
async def delete_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a milestone."""
    svc = _get_service(db, current_user)
    if not svc.delete_milestone(milestone_id):
        raise HTTPException(status_code=404, detail="Milestone not found")


@router.post("/milestones/{milestone_id}/toggle-completed", response_model=None)
async def toggle_milestone_completed(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Toggle milestone completed status."""
    svc = _get_service(db, current_user)
    milestone = svc.toggle_completed(milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return MilestoneResponse.model_validate(milestone).model_dump()
