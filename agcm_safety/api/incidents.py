"""API routes for Incident Reports"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_safety.schemas.incident import (
    IncidentReportCreate,
    IncidentReportUpdate,
    IncidentReportResponse,
)
from addons.agcm_safety.services.safety_service import SafetyService

router = APIRouter()


class InvestigateBody(BaseModel):
    root_cause: str = Field(..., max_length=5000)
    corrective_action: str = Field(..., max_length=5000)


class CloseBody(BaseModel):
    days_lost: int = Field(0, ge=0, le=9999)


def _get_service(db: Session, current_user) -> SafetyService:
    company_id = get_effective_company_id(current_user, db)
    return SafetyService(db, company_id, current_user.id)


@router.get("/incidents")
async def list_incidents(
    project_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List incident reports with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_incidents(project_id, severity, status, search, page, page_size)
    result["items"] = [IncidentReportResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/incidents/{incident_id}", response_model=IncidentReportResponse)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get an incident report."""
    svc = _get_service(db, current_user)
    incident = svc.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return incident


@router.post("/incidents", response_model=IncidentReportResponse, status_code=201)
async def create_incident(
    data: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new incident report."""
    svc = _get_service(db, current_user)
    incident = svc.create_incident(data)
    return incident


@router.put("/incidents/{incident_id}", response_model=IncidentReportResponse)
async def update_incident(
    incident_id: int,
    data: IncidentReportUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an incident report."""
    svc = _get_service(db, current_user)
    result = svc.update_incident(incident_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return result


@router.post("/incidents/{incident_id}/investigate", response_model=IncidentReportResponse)
async def investigate_incident(
    incident_id: int,
    body: InvestigateBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Start investigation on an incident with root cause and corrective action."""
    svc = _get_service(db, current_user)
    result = svc.investigate_incident(incident_id, body.root_cause, body.corrective_action)
    if not result:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return result


@router.post("/incidents/{incident_id}/close", response_model=IncidentReportResponse)
async def close_incident(
    incident_id: int,
    body: CloseBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Close an incident report."""
    svc = _get_service(db, current_user)
    result = svc.close_incident(incident_id, body.days_lost)
    if not result:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return result


@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an incident report."""
    svc = _get_service(db, current_user)
    if not svc.delete_incident(incident_id):
        raise HTTPException(status_code=404, detail="Incident report not found")
