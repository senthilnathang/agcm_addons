"""API routes for Report Definitions and Schedules"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_reporting.schemas.report_definition import (
    ReportDefinitionCreate,
    ReportDefinitionUpdate,
    ReportDefinitionResponse,
    ReportScheduleCreate,
    ReportScheduleUpdate,
    ReportScheduleResponse,
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
        page=page,
        page_size=page_size,
        report_type=report_type,
        search=search,
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
        raise HTTPException(
            status_code=404, detail="Report not found or is a system report"
        )
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
        raise HTTPException(
            status_code=404, detail="Report not found or is a system report"
        )


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
    format: str = Query("csv", description="Export format: csv, pdf, excel"),
    token: Optional[str] = Query(None, description="JWT token for browser downloads"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Export report data as a file download.
    Supports ?token=JWT for browser window.open() calls (no auth header).
    Supports CSV, PDF (via core pdf_service), and Excel formats.
    """
    # Resolve user from header or token query param
    if token:
        try:
            from app.core.security import decode_token, verify_token
            from app.models import User

            user_id = verify_token(token, "access")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            current_user = db.query(User).filter(User.id == user_id).first()
            if not current_user:
                raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    else:
        from app.api.deps.auth import get_current_user as _get_user

        current_user = _get_user(request=request, db=db)

    svc = _get_service(db, current_user)

    # PDF export via core pdf_service
    if format == "pdf":
        report = svc.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Execute report to get data
        result = svc.execute_report(report_id, None)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        # Build HTML report
        html = _build_report_html(report, result)

        # Generate PDF via core service
        try:
            from app.services.pdf_service import pdf_service

            return pdf_service.generate_or_fallback(
                html_content=html,
                filename=f"{report.name.replace(' ', '_')}.pdf",
                page_size="Letter",
                inline=False,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # CSV/Excel export
    result = svc.export_report(report_id, format)
    if not result:
        raise HTTPException(
            status_code=404, detail="Report not found or execution failed"
        )

    content, content_type, filename = result
    import io

    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _build_report_html(report, data):
    """Build an HTML document from report data for PDF rendering."""
    import html as html_mod
    from datetime import datetime

    esc = html_mod.escape
    rows = data.get("rows", data.get("data", []))
    columns = []
    if rows:
        columns = list(rows[0].keys()) if isinstance(rows[0], dict) else []

    # Parse column config from report
    try:
        import json

        col_config = (
            json.loads(report.columns)
            if isinstance(report.columns, str)
            else (report.columns or [])
        )
        if col_config and isinstance(col_config[0], str):
            columns = col_config
    except Exception:
        pass

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    h = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><style>
    @page {{ size: letter landscape; margin: 0.5in; }}
    body {{ font-family: Arial, sans-serif; font-size: 10px; color: #333; }}
    h1 {{ font-size: 16px; margin: 0 0 4px; }}
    .meta {{ font-size: 9px; color: #888; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th {{ background: #f5f5f5; font-weight: 600; text-align: left; padding: 5px 6px; border: 1px solid #ddd; font-size: 9px; }}
    td {{ padding: 4px 6px; border: 1px solid #e8e8e8; font-size: 9px; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    .footer {{ margin-top: 12px; font-size: 8px; color: #aaa; text-align: right; }}
    </style></head><body>
    <h1>{esc(report.name)}</h1>
    <div class="meta">{esc(report.description or "")} | Type: {esc(report.report_type or "")} | Generated: {esc(now)}</div>
    <table><thead><tr>"""

    for col in columns:
        h += f"<th>{esc(str(col))}</th>"
    h += "</tr></thead><tbody>"

    for row in rows:
        h += "<tr>"
        if isinstance(row, dict):
            for col in columns:
                h += f"<td>{esc(str(row.get(col, '')))}</td>"
        elif isinstance(row, (list, tuple)):
            for val in row:
                h += f"<td>{esc(str(val))}</td>"
        h += "</tr>"

    h += f'</tbody></table><div class="footer">Rows: {len(rows)} | {esc(now)}</div></body></html>'
    return h


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
