"""API routes for Takeoff Sheets and Measurements."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_estimate.schemas.estimate import (
    TakeoffSheetCreate, TakeoffSheetUpdate, TakeoffSheetResponse,
    TakeoffMeasurementCreate, TakeoffMeasurementUpdate, TakeoffMeasurementResponse,
)
from addons.agcm_estimate.services.estimate_service import EstimateService

router = APIRouter()


def _get_service(db: Session, current_user) -> EstimateService:
    company_id = get_effective_company_id(current_user, db)
    return EstimateService(db=db, company_id=company_id, user_id=current_user.id)


# =============================================================================
# TAKEOFF SHEETS
# =============================================================================

@router.get("/takeoff-sheets", response_model=None)
async def list_takeoff_sheets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List takeoff sheets with optional project filter."""
    svc = _get_service(db, current_user)
    return svc.list_takeoff_sheets(project_id=project_id, page=page, page_size=page_size)


@router.post("/takeoff-sheets", response_model=None, status_code=201)
async def create_takeoff_sheet(
    data: TakeoffSheetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new takeoff sheet."""
    svc = _get_service(db, current_user)
    sheet = svc.create_takeoff_sheet(data)
    return TakeoffSheetResponse.model_validate(sheet).model_dump()


@router.put("/takeoff-sheets/{sheet_id}", response_model=None)
async def update_takeoff_sheet(
    sheet_id: int,
    data: TakeoffSheetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a takeoff sheet."""
    svc = _get_service(db, current_user)
    sheet = svc.update_takeoff_sheet(sheet_id, data)
    if not sheet:
        raise HTTPException(status_code=404, detail="Takeoff sheet not found")
    return TakeoffSheetResponse.model_validate(sheet).model_dump()


@router.delete("/takeoff-sheets/{sheet_id}", status_code=204)
async def delete_takeoff_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a takeoff sheet."""
    svc = _get_service(db, current_user)
    if not svc.delete_takeoff_sheet(sheet_id):
        raise HTTPException(status_code=404, detail="Takeoff sheet not found")


# =============================================================================
# MEASUREMENTS
# =============================================================================

@router.get("/measurements", response_model=None)
async def list_measurements(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sheet_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List measurements with optional sheet filter."""
    svc = _get_service(db, current_user)
    return svc.list_measurements(sheet_id=sheet_id, page=page, page_size=page_size)


@router.post("/measurements", response_model=None, status_code=201)
async def create_measurement(
    data: TakeoffMeasurementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new measurement."""
    svc = _get_service(db, current_user)
    m = svc.create_measurement(data)
    return TakeoffMeasurementResponse.model_validate(m).model_dump()


@router.put("/measurements/{measurement_id}", response_model=None)
async def update_measurement(
    measurement_id: int,
    data: TakeoffMeasurementUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a measurement."""
    svc = _get_service(db, current_user)
    m = svc.update_measurement(measurement_id, data)
    if not m:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return TakeoffMeasurementResponse.model_validate(m).model_dump()


@router.delete("/measurements/{measurement_id}", status_code=204)
async def delete_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a measurement."""
    svc = _get_service(db, current_user)
    if not svc.delete_measurement(measurement_id):
        raise HTTPException(status_code=404, detail="Measurement not found")


@router.post("/measurements/{measurement_id}/link-to-line", response_model=None)
async def link_measurement_to_line(
    measurement_id: int,
    line_item_id: int = Query(..., description="Estimate line item ID to link to"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Link a measurement to an estimate line item."""
    svc = _get_service(db, current_user)
    m = svc.link_measurement_to_line(measurement_id, line_item_id)
    if not m:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return TakeoffMeasurementResponse.model_validate(m).model_dump()
