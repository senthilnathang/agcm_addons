"""API routes for Report Definitions and Schedules"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_reporting.schemas.report_definition import (
    ReportDefinitionCreate, ReportDefinitionUpdate, ReportDefinitionResponse,
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse,
)
from addons.agcm_reporting.services.reporting_service import ReportingService

router = APIRouter()


def _get_service(db: Session, current_user) -> ReportingService:
    company_id = get_effective_company_id(current_user, db)
    return ReportingService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/reports", response_model=None)
async def list_reports(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    report_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List report definitions with pagination."""
    svc = _get_service(db, current_user)
    return svc.list_reports(
        page=page, page_size=page_size,
        report_type=report_type, search=search,
    )


@router.get("/reports/{report_id}", response_model=None)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get report definition with schedules."""
    svc = _get_service(db, current_user)
    report = svc.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportDefinitionResponse.model_validate(report).model_dump()


@router.post("/reports", response_model=None, status_code=201)
async def create_report(
    data: ReportDefinitionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new report definition."""
    svc = _get_service(db, current_user)
    report = svc.create_report(data)
    return ReportDefinitionResponse.model_validate(report).model_dump()


@router.put("/reports/{report_id}", response_model=None)
async def update_report(
    report_id: int,
    data: ReportDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a report definition."""
    svc = _get_service(db, current_user)
    report = svc.update_report(report_id, data)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or is a system report")
    return ReportDefinitionResponse.model_validate(report).model_dump()


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a report definition."""
    svc = _get_service(db, current_user)
    if not svc.delete_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found or is a system report")


@router.post("/reports/{report_id}/execute", response_model=None)
async def execute_report(
    report_id: int,
    filters: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Execute a report and return data."""
    svc = _get_service(db, current_user)
    result = svc.execute_report(report_id, filters)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/reports/{report_id}/export", response_model=None)
async def export_report(
    report_id: int,
    format: str = Query("csv", description="Export format: csv"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export report data as a file."""
    svc = _get_service(db, current_user)
    result = svc.export_report(report_id, format)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found or execution failed")

    content, content_type, filename = result
    import io
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- Schedules ---

@router.post("/reports/{report_id}/schedules", response_model=None, status_code=201)
async def create_schedule(
    report_id: int,
    data: ReportScheduleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a schedule to a report."""
    svc = _get_service(db, current_user)
    schedule = svc.create_schedule(report_id, data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportScheduleResponse.model_validate(schedule).model_dump()


@router.put("/schedules/{schedule_id}", response_model=None)
async def update_schedule(
    schedule_id: int,
    data: ReportScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a report schedule."""
    svc = _get_service(db, current_user)
    schedule = svc.update_schedule(schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ReportScheduleResponse.model_validate(schedule).model_dump()


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a report schedule."""
    svc = _get_service(db, current_user)
    if not svc.delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
