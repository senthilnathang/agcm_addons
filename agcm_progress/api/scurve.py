"""API routes for S-Curve"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_progress.schemas.progress import (
    SCurveDataCreate, SCurveDataUpdate, SCurveDataResponse,
)
from addons.agcm_progress.services.progress_service import ProgressService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProgressService:
    company_id = get_effective_company_id(current_user, db)
    return ProgressService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/scurve", response_model=None)
async def get_scurve_data(
    project_id: int = Query(..., description="Filter by project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get S-curve chart data (all date points sorted by date)."""
    svc = _get_service(db, current_user)
    items = svc.get_scurve_chart_data(project_id)
    return {"items": items}


@router.post("/scurve", response_model=None, status_code=201)
async def create_scurve_data(
    data: SCurveDataCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new S-curve data point."""
    svc = _get_service(db, current_user)
    try:
        scurve = svc.create_scurve_data(data)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="S-curve data point already exists for this project and date",
            )
        raise
    return SCurveDataResponse.model_validate(scurve).model_dump()


@router.put("/scurve/{scurve_id}", response_model=None)
async def update_scurve_data(
    scurve_id: int,
    data: SCurveDataUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an S-curve data point."""
    svc = _get_service(db, current_user)
    scurve = svc.update_scurve_data(scurve_id, data)
    if not scurve:
        raise HTTPException(status_code=404, detail="S-curve data point not found")
    return SCurveDataResponse.model_validate(scurve).model_dump()


@router.delete("/scurve/{scurve_id}", status_code=204)
async def delete_scurve_data(
    scurve_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an S-curve data point."""
    svc = _get_service(db, current_user)
    if not svc.delete_scurve_data(scurve_id):
        raise HTTPException(status_code=404, detail="S-curve data point not found")
