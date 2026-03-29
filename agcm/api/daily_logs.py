"""API routes for DailyActivityLog and all child entities"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id, PaginationParams, get_pagination

from addons.agcm.models.project import Project
from addons.agcm.models.daily_activity_log import DailyActivityLog
from addons.agcm.models.manpower import ManPower
from addons.agcm.models.notes import Notes
from addons.agcm.models.inspection import Inspection
from addons.agcm.models.accident import Accident
from addons.agcm.models.visitor import Visitor
from addons.agcm.models.safety_violation import SafetyViolation
from addons.agcm.models.delay import Delay
from addons.agcm.models.deficiency import Deficiency
from addons.agcm.models.photo import Photo

from addons.agcm.schemas.daily_activity_log import (
    DailyActivityLogCreate, DailyActivityLogUpdate, DailyActivityLogResponse,
    MakeLogRequest,
    ManPowerCreate, ManPowerUpdate, ManPowerResponse,
    NotesCreate, NotesUpdate, NotesResponse,
    InspectionCreate, InspectionUpdate, InspectionResponse,
    AccidentCreate, AccidentUpdate, AccidentResponse,
    VisitorCreate, VisitorUpdate, VisitorResponse,
    SafetyViolationCreate, SafetyViolationUpdate, SafetyViolationResponse,
    DelayCreate, DelayUpdate, DelayResponse,
    DeficiencyCreate, DeficiencyUpdate, DeficiencyResponse,
    PhotoCreate, PhotoUpdate, PhotoResponse,
    WeatherForecastResponse,
)
from addons.agcm.services.daily_activity_log_service import DailyActivityLogService

router = APIRouter()


def _get_service(db: Session, current_user) -> DailyActivityLogService:
    company_id = get_effective_company_id(current_user, db)
    return DailyActivityLogService(db=db, company_id=company_id, user_id=current_user.id)


# =========================================================================
# Daily Activity Log CRUD
# =========================================================================

@router.get("/daily-logs", response_model=None)
async def list_daily_logs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    project_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    """List daily activity logs with filters."""
    svc = _get_service(db, current_user)
    return svc.list_logs(
        page=pagination.page,
        page_size=pagination.page_size,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/daily-logs/{log_id}", response_model=None)
async def get_daily_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get daily log with child entity counts."""
    svc = _get_service(db, current_user)
    detail = svc.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return detail


@router.post("/daily-logs", response_model=None, status_code=201)
async def create_daily_log(
    data: DailyActivityLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new daily activity log."""
    svc = _get_service(db, current_user)
    try:
        log = svc.create_log(project_id=data.project_id, log_date=data.date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DailyActivityLogResponse.model_validate(log).model_dump()


@router.put("/daily-logs/{log_id}", response_model=None)
async def update_daily_log(
    log_id: int,
    data: DailyActivityLogUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a daily log."""
    svc = _get_service(db, current_user)
    try:
        log = svc.update_log(
            log_id,
            log_date=data.date,
            project_id=data.project_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return DailyActivityLogResponse.model_validate(log).model_dump()


@router.delete("/daily-logs/{log_id}", status_code=204)
async def delete_daily_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a daily log and all its children."""
    svc = _get_service(db, current_user)
    if not svc.delete_log(log_id):
        raise HTTPException(status_code=404, detail="Daily log not found")


@router.post("/daily-logs/makelog", response_model=None, status_code=201)
async def makelog(
    data: MakeLogRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Copy a daily log with selective child entity copying.
    Equivalent to Odoo's makelog button.
    """
    svc = _get_service(db, current_user)
    try:
        new_log = svc.makelog(
            source_log_id=data.source_log_id,
            target_date=data.date,
            copy_manpower=data.copy_manpower,
            copy_safety=data.copy_safety,
            copy_observations=data.copy_observations,
            copy_inspections=data.copy_inspections,
            copy_delays=data.copy_delays,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DailyActivityLogResponse.model_validate(new_log).model_dump()


# =========================================================================
# PDF Report Export
# =========================================================================

from addons.agcm.models.weather import Weather, WeatherForecast
from addons.agcm.models.lookups import InspectionType, AccidentType, ViolationType


def _render_report_html(db, log, project, current_user):
    """Render the daily log report as HTML matching the Odoo PDF layout exactly."""

    # Fetch all child entities
    manpower_lines = db.query(ManPower).filter(ManPower.dailylog_id == log.id).all()
    notes_lines = db.query(Notes).filter(Notes.dailylog_id == log.id).all()
    inspection_lines = db.query(Inspection).filter(Inspection.dailylog_id == log.id).all()
    accident_lines = db.query(Accident).filter(Accident.dailylog_id == log.id).all()
    visitor_lines = db.query(Visitor).filter(Visitor.dailylog_id == log.id).all()
    safety_lines = db.query(SafetyViolation).filter(SafetyViolation.dailylog_id == log.id).all()
    delay_lines = db.query(Delay).filter(Delay.dailylog_id == log.id).all()
    deficiency_lines = db.query(Deficiency).filter(Deficiency.dailylog_id == log.id).all()
    photo_lines = db.query(Photo).filter(Photo.dailylog_id == log.id).all()
    forecast_lines = db.query(WeatherForecast).filter(WeatherForecast.dailylog_id == log.id).order_by(WeatherForecast.time_interval).all()

    from app.models import User
    def user_name(uid):
        if not uid:
            return ''
        u = db.query(User).filter(User.id == uid).first()
        return u.full_name or u.username or u.email if u else ''

    def inspection_type_name(tid):
        if not tid:
            return ''
        t = db.query(InspectionType).filter(InspectionType.id == tid).first()
        return t.name if t else ''

    weather_code_labels = {1: 'Clear', 2: 'Cloudy', 3: 'Light Rain', 4: 'Heavy Rain', 5: 'Thunder'}
    report_date_formatted = log.date.strftime('%A, %d %B %Y') if log.date else ''
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    photo_pairs = [photo_lines[i:i+2] for i in range(0, len(photo_lines), 2)]

    # Company info from DB (logo, name, address)
    from app.models.company import Company
    company = db.query(Company).filter(Company.id == project.company_id).first()
    company_name = company.name if company else ''
    company_address = company.address or '' if company else ''
    company_city_state = ''
    if company:
        parts = [p for p in [company.city, company.state, company.zip_code] if p]
        company_city_state = ', '.join(parts)
    company_logo_url = (company.logo_url or '') if company else ''

    def esc(val):
        if val is None:
            return ''
        return str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    h = []

    # --- Page Shell ---
    h.append(f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  @page {{
    size: letter;
    margin: 0.75in 0.6in 1.3in 0.6in;
  }}
  @media print {{
    .page-footer {{ position: fixed; bottom: 0; left: 0; right: 0; }}
    .page-header {{ position: fixed; top: 0; left: 0; right: 0; }}
    body {{ margin-top: 100px; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px;
    color: #222;
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.5in 0.6in;
    background: #fff;
  }}

  /* ── Header ── */
  .report-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 30px;
    min-height: 80px;
  }}
  .logo-block {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }}
  .company-logo {{
    max-height: 60px;
    max-width: 180px;
    object-fit: contain;
  }}
  .company-name {{
    font-size: 18px;
    font-weight: bold;
    color: #222;
    margin-bottom: 2px;
  }}
  .company-addr {{
    font-size: 10px;
    color: #333;
    line-height: 1.5;
    margin-top: 4px;
  }}
  .project-info {{
    text-align: right;
    font-size: 11px;
    color: #333;
    line-height: 1.6;
  }}

  /* ── Title ── */
  .report-title {{
    font-size: 22px;
    font-weight: bold;
    color: #000;
    border-top: 1px solid #000;
    padding-top: 12px;
    margin: 0 0 20px 0;
  }}

  /* ── Section headers ── */
  h4.section-title {{
    font-size: 15px;
    font-weight: bold;
    color: #000;
    margin: 22px 0 6px 0;
    padding: 0;
  }}

  /* ── Tables ── */
  .report-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 18px;
    font-size: 10.5px;
  }}
  .report-table th {{
    background-color: #D3D3D3;
    text-align: left;
    padding: 5px 8px;
    font-weight: normal;
    font-size: 10.5px;
    border: none;
  }}
  .report-table td {{
    padding: 5px 8px;
    border-bottom: 1px solid #ddd;
    font-size: 10.5px;
    vertical-align: top;
  }}

  /* ── Photos ── */
  .photo-grid {{
    width: 100%;
    border-collapse: collapse;
  }}
  .photo-grid td {{
    width: 48%;
    vertical-align: top;
    padding: 8px 10px;
  }}
  .photo-grid img {{
    width: 100%;
    max-width: 380px;
    height: auto;
    max-height: 320px;
    object-fit: contain;
    display: block;
  }}
  .photo-caption {{
    font-size: 10px;
    color: #333;
    margin-top: 6px;
    padding-bottom: 10px;
  }}

  /* ── Footer ── */
  .report-footer {{
    border-top: 1px solid #000;
    margin-top: 40px;
    padding-top: 6px;
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #333;
  }}
  .footer-left {{ text-align: left; }}
  .footer-right {{ text-align: right; }}
</style>
</head>
<body>

<!-- ════════ HEADER ════════ -->
<div class="report-header">
  <div class="logo-block">
    <div>
      {'<img class="company-logo" src="' + esc(company_logo_url) + '" alt="Logo"/>' if company_logo_url else '<div class="company-name">' + esc(company_name) + '</div>'}
      <div class="company-addr">
        {esc(company_name)}<br/>
        {esc(company_address)}<br/>
        {esc(company_city_state)}
      </div>
    </div>
  </div>
  <div class="project-info">
    <div>Project : <strong>{esc(project.name)}</strong></div>
    <div>{esc(project.street or '')}</div>
    <div>{esc(project.city or '')} {esc(project.state or '')}</div>
  </div>
</div>

<!-- ════════ TITLE ════════ -->
<div class="report-title">Site Observation Report:&nbsp;&nbsp;{esc(report_date_formatted)}</div>
''')

    # --- Weather Forecast Snapshot ---
    if forecast_lines:
        h.append('<h4 class="section-title">Daily Snapshot</h4>')
        h.append('<table class="report-table"><thead><tr>')
        for f in forecast_lines:
            interval = f.time_interval or ''
            label = interval
            if 'T' in str(interval):
                hour = int(str(interval).split('T')[1].split(':')[0])
                if hour <= 6: label = '6 AM'
                elif hour <= 9: label = '9 AM'
                elif hour <= 12: label = '12 PM'
                elif hour <= 15: label = '3 PM'
                elif hour <= 18: label = '6 PM'
                else: label = '9 PM'
            h.append(f'<th>{esc(label)}</th>')
        h.append('</tr></thead><tbody><tr>')
        for f in forecast_lines:
            wlabel = weather_code_labels.get(f.weather_code, 'N/A')
            h.append(f'<td>{f.temperature or 0:.0f} F {esc(wlabel)}</td>')
        h.append('</tr></tbody></table>')

    # --- Manpower ---
    if manpower_lines:
        h.append('<h4 class="section-title">Manpower Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Comments</th><th>Location</th><th>Number Of Workers</th>'
                 '<th>Total Hours</th><th>Vendor</th>'
                 '</tr></thead><tbody>')
        for m in manpower_lines:
            h.append(f'<tr><td>{esc(m.name)}</td><td>{esc(m.location)}</td>'
                     f'<td>{m.number_of_workers}</td><td>{m.total_hours}</td>'
                     f'<td>{esc(user_name(m.partner_id))}</td></tr>')
        h.append('</tbody></table>')

    # --- Notes ---
    if notes_lines:
        h.append('<h4 class="section-title">Notes Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Comments</th><th>Description</th>'
                 '</tr></thead><tbody>')
        for n in notes_lines:
            h.append(f'<tr><td>{esc(n.name)}</td><td>{esc(n.description)}</td></tr>')
        h.append('</tbody></table>')

    # --- Inspections ---
    if inspection_lines:
        h.append('<h4 class="section-title">Inspection Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Inspection Type</th><th>Result</th>'
                 '</tr></thead><tbody>')
        for i in inspection_lines:
            h.append(f'<tr><td>{esc(inspection_type_name(i.inspection_type_id))}</td>'
                     f'<td>{esc(i.result)}</td></tr>')
        h.append('</tbody></table>')

    # --- Visitors ---
    if visitor_lines:
        h.append('<h4 class="section-title">Visitors Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Visitor Name</th><th>Reason</th><th>Entry Time</th>'
                 '<th>Exit Time</th><th>Person to Meet</th><th>Comments</th>'
                 '</tr></thead><tbody>')
        for v in visitor_lines:
            entry = v.visit_entry_time.strftime('%Y-%m-%d %H:%M') if v.visit_entry_time else ''
            exit_ = v.visit_exit_time.strftime('%Y-%m-%d %H:%M') if v.visit_exit_time else ''
            h.append(f'<tr><td>{esc(v.name)}</td><td>{esc(v.reason)}</td>'
                     f'<td>{esc(entry)}</td><td>{esc(exit_)}</td>'
                     f'<td>{esc(user_name(v.user_id))}</td><td>{esc(v.comments)}</td></tr>')
        h.append('</tbody></table>')

    # --- Safety Observations ---
    if safety_lines:
        h.append('<h4 class="section-title">Safety Observations</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Description</th><th>Observation Notice</th>'
                 '</tr></thead><tbody>')
        for s in safety_lines:
            h.append(f'<tr><td>{esc(s.name)}</td><td>{esc(s.violation_notice)}</td></tr>')
        h.append('</tbody></table>')

    # --- Delays ---
    if delay_lines:
        h.append('<h4 class="section-title">Delay Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Name</th><th>Reason</th><th>Delay</th><th>Contractor</th>'
                 '</tr></thead><tbody>')
        for d in delay_lines:
            h.append(f'<tr><td>{esc(d.name)}</td><td>{esc(d.reason)}</td>'
                     f'<td>{esc(d.delay)}</td><td>{esc(user_name(d.partner_id))}</td></tr>')
        h.append('</tbody></table>')

    # --- Deficiencies ---
    if deficiency_lines:
        h.append('<h4 class="section-title">Deficiency Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Name</th><th>Description</th>'
                 '</tr></thead><tbody>')
        for d in deficiency_lines:
            h.append(f'<tr><td>{esc(d.name)}</td><td>{esc(d.description)}</td></tr>')
        h.append('</tbody></table>')

    # --- Accidents ---
    if accident_lines:
        h.append('<h4 class="section-title">Accident Report</h4>')
        h.append('<table class="report-table"><thead><tr>'
                 '<th>Description</th><th>Location</th><th>Resolution</th>'
                 '</tr></thead><tbody>')
        for a in accident_lines:
            h.append(f'<tr><td>{esc(a.name)}</td><td>{esc(a.location)}</td>'
                     f'<td>{esc(a.resolution)}</td></tr>')
        h.append('</tbody></table>')

    # --- Photos (2-column grid matching Odoo layout) ---
    if photo_lines:
        h.append('<h4 class="section-title">Photos</h4>')
        h.append('<table class="photo-grid"><tbody>')
        for pair in photo_pairs:
            h.append('<tr>')
            for p in pair:
                img_tag = ''
                if p.file_url:
                    img_tag = f'<img src="{esc(p.file_url)}" />'
                h.append(f'<td>{img_tag}<div class="photo-caption">{esc(p.name)}</div></td>')
            if len(pair) == 1:
                h.append('<td></td>')
            h.append('</tr>')
        h.append('</tbody></table>')

    # --- Footer (visible in HTML view; @page CSS handles print) ---
    h.append(f'''
<div class="report-footer">
  <div class="footer-left">
    <div><strong>Project Name:</strong> {esc(project.name)}</div>
    <div>Report Date: {esc(str(log.date))}</div>
  </div>
  <div class="footer-right">
    <div>By: {esc(user_name(current_user.id))}</div>
    <div>Printed On: {esc(now_str)}</div>
  </div>
</div>

</body>
</html>''')

    return ''.join(h)


from fastapi import Request
from app.api.deps.auth import get_optional_user


def _resolve_report_user(request: Request, db: Session, token: Optional[str] = None):
    """
    Resolve user for report endpoints.
    Accepts auth via:
      1. Standard Authorization header (normal API flow)
      2. ?token= query param (browser new-tab flow)
    """
    from app.api.deps.auth import decode_token
    from app.models import User

    # Try header first
    auth_header = request.headers.get("authorization", "")
    jwt_token = None
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    elif token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(jwt_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/daily-logs/{log_id}/report/pdf")
async def export_daily_log_pdf(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Query(None, description="JWT token for browser-tab access"),
):
    """Export daily log as PDF report matching the Odoo report layout."""
    current_user = _resolve_report_user(request, db, token)
    svc = _get_service(db, current_user)
    log = svc.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    project = db.query(Project).filter(Project.id == log.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    html_content = _render_report_html(db, log, project, current_user)

    # Try WeasyPrint first, fall back to returning HTML
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_bytes = WeasyHTML(string=html_content).write_pdf()
        filename = f"Daily Log - {log.date} - {log.sequence_name}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        # WeasyPrint not installed — return HTML for browser print
        return Response(content=html_content, media_type="text/html")


@router.get("/daily-logs/{log_id}/report/html")
async def export_daily_log_html(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Query(None, description="JWT token for browser-tab access"),
):
    """Export daily log as printable HTML (browser print to PDF fallback)."""
    current_user = _resolve_report_user(request, db, token)
    svc = _get_service(db, current_user)
    log = svc.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    project = db.query(Project).filter(Project.id == log.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    html_content = _render_report_html(db, log, project, current_user)
    return Response(content=html_content, media_type="text/html")


# =========================================================================
# Periodic Project Report — multiple daily logs in one document
# =========================================================================

@router.get("/reports/periodic")
async def periodic_project_report(
    project_id: int = Query(...),
    request: Request = None,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Generate a combined report of all daily logs for a project within a date range.
    Each daily log renders as a full page, concatenated into one HTML document.
    """
    current_user = _resolve_report_user(request, db, token)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch logs in date range
    log_q = db.query(DailyActivityLog).filter(DailyActivityLog.project_id == project_id)
    if date_from:
        log_q = log_q.filter(DailyActivityLog.date >= date_from)
    if date_to:
        log_q = log_q.filter(DailyActivityLog.date <= date_to)
    logs = log_q.order_by(DailyActivityLog.date).all()

    if not logs:
        raise HTTPException(status_code=404, detail="No daily logs found for the selected criteria")

    # Render each log's HTML body (strip <html>/<head>/<body> tags — just inner content)
    all_pages = []
    for log in logs:
        page_html = _render_report_html(db, log, project, current_user)
        # Extract just the body content between <body> and </body>
        body_start = page_html.find('<body>') + 6
        body_end = page_html.find('</body>')
        if body_start > 5 and body_end > 0:
            all_pages.append(page_html[body_start:body_end])
        else:
            all_pages.append(page_html)

    # Extract CSS from the first page
    css_start = page_html.find('<style>')
    css_end = page_html.find('</style>') + 8
    css_block = page_html[css_start:css_end] if css_start >= 0 else ''

    # Build combined document
    date_range_str = ""
    if date_from and date_to:
        date_range_str = f"{date_from} to {date_to}"
    elif date_from:
        date_range_str = f"from {date_from}"
    elif date_to:
        date_range_str = f"up to {date_to}"
    else:
        date_range_str = "All dates"

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    combined = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Project Report - {project.name}</title>
{css_block}
<style>
  .page-break {{ page-break-before: always; }}
  .report-cover {{
    text-align: center;
    padding: 120px 40px;
    border-bottom: 2px solid #333;
    margin-bottom: 40px;
  }}
  .report-cover h1 {{ font-size: 28px; color: #222; margin-bottom: 8px; }}
  .report-cover h2 {{ font-size: 20px; color: #555; font-weight: normal; }}
  .report-cover .meta {{ color: #888; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>

<!-- Cover Page -->
<div class="report-cover">
  <h1>Periodic Project Report</h1>
  <h2>{project.name}</h2>
  <p style="font-size:14px; color:#555;">{project.ref_number} | {project.city or ""}, {project.state or ""}</p>
  <p style="font-size:13px; color:#666;">Date Range: {date_range_str}</p>
  <p style="font-size:13px; color:#666;">{len(logs)} Daily Log(s)</p>
  <div class="meta">
    Generated on: {now_str}
  </div>
</div>

'''
    for i, page in enumerate(all_pages):
        if i > 0:
            combined += '<div class="page-break"></div>\n'
        combined += page + '\n'

    combined += '</body></html>'

    filename = f"Project Report - {project.name} - {date_range_str}.html"
    return Response(content=combined, media_type="text/html")


# =========================================================================
# Generic child entity CRUD factory
# =========================================================================

def _child_crud_routes(
    prefix: str,
    model_class,
    create_schema,
    update_schema,
    response_schema,
):
    """Generate standard CRUD routes for a daily log child entity."""

    @router.get(f"/{prefix}", response_model=None)
    async def list_items(
        dailylog_id: int = Query(..., description="Daily log ID"),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        pagination: PaginationParams = Depends(get_pagination),
    ):
        svc = _get_service(db, current_user)
        return svc.list_children(model_class, dailylog_id, pagination.page, pagination.page_size)

    @router.get(f"/{prefix}/{{record_id}}", response_model=None)
    async def get_item(
        record_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        svc = _get_service(db, current_user)
        record = svc.get_child(model_class, record_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"{prefix} not found")
        return response_schema.model_validate(record).model_dump()

    @router.post(f"/{prefix}", response_model=None, status_code=201)
    async def create_item(
        data: create_schema,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        svc = _get_service(db, current_user)
        record = svc.create_child(model_class, data.model_dump())
        return response_schema.model_validate(record).model_dump()

    @router.put(f"/{prefix}/{{record_id}}", response_model=None)
    async def update_item(
        record_id: int,
        data: update_schema,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        svc = _get_service(db, current_user)
        update_data = data.model_dump(exclude_unset=True)
        record = svc.update_child(model_class, record_id, update_data)
        if not record:
            raise HTTPException(status_code=404, detail=f"{prefix} not found")
        return response_schema.model_validate(record).model_dump()

    @router.delete(f"/{prefix}/{{record_id}}", status_code=204)
    async def delete_item(
        record_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        svc = _get_service(db, current_user)
        if not svc.delete_child(model_class, record_id):
            raise HTTPException(status_code=404, detail=f"{prefix} not found")

    # Rename functions to avoid FastAPI route conflicts
    list_items.__name__ = f"list_{prefix}"
    get_item.__name__ = f"get_{prefix}"
    create_item.__name__ = f"create_{prefix}"
    update_item.__name__ = f"update_{prefix}"
    delete_item.__name__ = f"delete_{prefix}"


# Register CRUD routes for all child entities
_child_crud_routes("manpower", ManPower, ManPowerCreate, ManPowerUpdate, ManPowerResponse)
_child_crud_routes("notes", Notes, NotesCreate, NotesUpdate, NotesResponse)
_child_crud_routes("inspections", Inspection, InspectionCreate, InspectionUpdate, InspectionResponse)
_child_crud_routes("accidents", Accident, AccidentCreate, AccidentUpdate, AccidentResponse)
_child_crud_routes("visitors", Visitor, VisitorCreate, VisitorUpdate, VisitorResponse)
_child_crud_routes("safety-violations", SafetyViolation, SafetyViolationCreate, SafetyViolationUpdate, SafetyViolationResponse)
_child_crud_routes("delays", Delay, DelayCreate, DelayUpdate, DelayResponse)
_child_crud_routes("deficiencies", Deficiency, DeficiencyCreate, DeficiencyUpdate, DeficiencyResponse)
_child_crud_routes("photos", Photo, PhotoCreate, PhotoUpdate, PhotoResponse)
