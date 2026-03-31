"""API routes for Inspections"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_safety.schemas.inspection import (
    InspectionCreate,
    InspectionUpdate,
    InspectionResponse,
    InspectionDetail,
)
from addons.agcm_safety.services.safety_service import SafetyService

router = APIRouter()


class CompleteInspectionBody(BaseModel):
    overall_result: str = Field(..., max_length=20)  # pass, fail, conditional


def _get_service(db: Session, current_user) -> SafetyService:
    company_id = get_effective_company_id(current_user, db)
    return SafetyService(db, company_id, current_user.id)


@router.get("/inspections")
async def list_inspections(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List inspections with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_inspections(project_id, status, search, page, page_size)
    result["items"] = [InspectionResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/inspections/{inspection_id}", response_model=InspectionDetail)
async def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get inspection details with checklist items."""
    svc = _get_service(db, current_user)
    detail = svc.get_inspection_detail(inspection_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return detail


@router.post("/inspections", response_model=InspectionResponse, status_code=201)
async def create_inspection(
    data: InspectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new inspection. If template_id is provided, items are pre-populated from the template."""
    svc = _get_service(db, current_user)
    if data.template_id:
        insp = svc.create_inspection_from_template(data.project_id, data.template_id, data)
        if not insp:
            raise HTTPException(status_code=404, detail="Checklist template not found")
    else:
        insp = svc.create_inspection(data)
    return insp


@router.put("/inspections/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: int,
    data: InspectionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an inspection."""
    svc = _get_service(db, current_user)
    result = svc.update_inspection(inspection_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.post("/inspections/{inspection_id}/start", response_model=InspectionResponse)
async def start_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Start an inspection (set status to in_progress)."""
    svc = _get_service(db, current_user)
    result = svc.start_inspection(inspection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.post("/inspections/{inspection_id}/complete", response_model=InspectionResponse)
async def complete_inspection(
    inspection_id: int,
    body: CompleteInspectionBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Complete an inspection with an overall result (pass, fail, conditional)."""
    svc = _get_service(db, current_user)
    result = svc.complete_inspection(inspection_id, body.overall_result)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.delete("/inspections/{inspection_id}", status_code=204)
async def delete_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an inspection."""
    svc = _get_service(db, current_user)
    if not svc.delete_inspection(inspection_id):
        raise HTTPException(status_code=404, detail="Inspection not found")
