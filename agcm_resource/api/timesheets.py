"""API routes for Timesheets"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_resource.schemas.resource import TimesheetCreate, TimesheetUpdate, TimesheetResponse
from addons.agcm_resource.services.resource_service import ResourceService

router = APIRouter()


def _get_service(db: Session, current_user) -> ResourceService:
    company_id = get_effective_company_id(current_user, db)
    return ResourceService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/timesheets", response_model=None)
async def list_timesheets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    worker_id: Optional[int] = Query(None, description="Filter by worker"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    status: Optional[str] = Query(None, description="Filter by status: draft, submitted, approved, rejected"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, description="Search by sequence, task, location"),
):
    """List timesheets with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_timesheets(
        page=page, page_size=page_size,
        worker_id=worker_id, project_id=project_id,
        status=status, date_from=date_from, date_to=date_to,
        search=search,
    )


@router.get("/timesheets/{timesheet_id}", response_model=None)
async def get_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get timesheet details."""
    svc = _get_service(db, current_user)
    timesheet = svc.get_timesheet(timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    return TimesheetResponse.model_validate(timesheet).model_dump()


@router.post("/timesheets", response_model=None, status_code=201)
async def create_timesheet(
    data: TimesheetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new timesheet entry."""
    svc = _get_service(db, current_user)
    timesheet = svc.create_timesheet(data)
    return TimesheetResponse.model_validate(timesheet).model_dump()


@router.put("/timesheets/{timesheet_id}", response_model=None)
async def update_timesheet(
    timesheet_id: int,
    data: TimesheetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a timesheet (only if draft or rejected)."""
    svc = _get_service(db, current_user)
    timesheet = svc.update_timesheet(timesheet_id, data)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found or cannot be edited")
    return TimesheetResponse.model_validate(timesheet).model_dump()


@router.delete("/timesheets/{timesheet_id}", status_code=204)
async def delete_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a timesheet (only if not approved)."""
    svc = _get_service(db, current_user)
    if not svc.delete_timesheet(timesheet_id):
        raise HTTPException(status_code=404, detail="Timesheet not found or cannot be deleted")


@router.post("/timesheets/{timesheet_id}/submit", response_model=None)
async def submit_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit a draft timesheet for approval."""
    svc = _get_service(db, current_user)
    timesheet = svc.submit_timesheet(timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=400, detail="Timesheet not found or not in draft status")
    return TimesheetResponse.model_validate(timesheet).model_dump()


@router.post("/timesheets/{timesheet_id}/approve", response_model=None)
async def approve_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a submitted timesheet."""
    svc = _get_service(db, current_user)
    timesheet = svc.approve_timesheet(timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=400, detail="Timesheet not found or not in submitted status")
    return TimesheetResponse.model_validate(timesheet).model_dump()


@router.post("/timesheets/{timesheet_id}/reject", response_model=None)
async def reject_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject a submitted timesheet."""
    svc = _get_service(db, current_user)
    timesheet = svc.reject_timesheet(timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=400, detail="Timesheet not found or not in submitted status")
    return TimesheetResponse.model_validate(timesheet).model_dump()
