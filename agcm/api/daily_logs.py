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


def _render_overview_canvas(
    log, project, manpower_lines, notes_lines, inspection_lines,
    accident_lines, visitor_lines, safety_lines, delay_lines,
    deficiency_lines, photo_lines, forecast_lines,
    weather_code_labels, esc,
):
    """Render the Overview Canvas — a graphical dashboard page inserted after the title."""

    # ── Compute metrics ──
    total_workers = sum(m.number_of_workers or 0 for m in manpower_lines)
    total_hours = sum(m.total_hours or 0 for m in manpower_lines)
    total_inspections = len(inspection_lines)
    total_visitors = len(visitor_lines)
    total_safety = len(safety_lines) + len(accident_lines)
    total_delays = len(delay_lines)
    total_deficiencies = len(deficiency_lines)
    total_notes = len(notes_lines)
    total_photos = len(photo_lines)

    # Weather average
    temps = [f.temperature for f in forecast_lines if f.temperature]
    avg_temp = round(sum(temps) / len(temps), 1) if temps else 0
    humidities = [f.humidity for f in forecast_lines if f.humidity]
    avg_humidity = round(sum(humidities) / len(humidities), 1) if humidities else 0
    winds = [f.wind for f in forecast_lines if f.wind]
    avg_wind = round(sum(winds) / len(winds), 1) if winds else 0
    weather_dominant = ""
    if forecast_lines:
        codes = [f.weather_code for f in forecast_lines if f.weather_code]
        if codes:
            from collections import Counter
            most_common = Counter(codes).most_common(1)[0][0]
            weather_dominant = weather_code_labels.get(most_common, "")

    # ── Activity distribution for donut chart (SVG) ──
    activities = [
        ("Manpower", len(manpower_lines), "#1890ff"),
        ("Notes", total_notes, "#722ed1"),
        ("Inspections", total_inspections, "#13c2c2"),
        ("Visitors", total_visitors, "#52c41a"),
        ("Safety", total_safety, "#ff4d4f"),
        ("Delays", total_delays, "#faad14"),
        ("Deficiencies", total_deficiencies, "#fa541c"),
        ("Photos", total_photos, "#2f54eb"),
    ]
    activity_total = sum(a[1] for a in activities)

    # Build SVG donut chart (pure inline SVG — no JS needed for PDF)
    donut_svg = _build_donut_svg(activities, activity_total)

    # Build temperature bar chart SVG
    temp_svg = _build_temp_bar_svg(forecast_lines, weather_code_labels)

    # Build inspection result bar
    pass_count = sum(1 for i in inspection_lines if (i.result or "").lower() in ("pass", "passed"))
    fail_count = sum(1 for i in inspection_lines if (i.result or "").lower() in ("fail", "failed"))
    other_count = total_inspections - pass_count - fail_count
    inspection_bar = _build_inspection_bar(pass_count, fail_count, other_count, total_inspections)

    # ── Build HTML ──
    html = f'''
<!-- ════════ OVERVIEW CANVAS ════════ -->
<div style="page-break-after: always; padding-top: 8px;">
  <h4 style="font-size: 14px; color: #1a1a1a; border-bottom: 2px solid #1890ff; padding-bottom: 4px; margin: 0 0 12px 0;">
    Daily Overview Dashboard
  </h4>

  <!-- KPI Cards Row -->
  <table style="width: 100%; border-collapse: separate; border-spacing: 8px 0; margin-bottom: 14px;">
    <tr>
      <td style="width: 16.6%; background: #f0f5ff; border: 1px solid #d6e4ff; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #1890ff;">{total_workers}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Workers</div>
      </td>
      <td style="width: 16.6%; background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #52c41a;">{total_hours:.0f}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Total Hours</div>
      </td>
      <td style="width: 16.6%; background: #e6fffb; border: 1px solid #87e8de; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #13c2c2;">{total_inspections}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Inspections</div>
      </td>
      <td style="width: 16.6%; background: #fff2e8; border: 1px solid #ffbb96; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #fa541c;">{total_deficiencies}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Deficiencies</div>
      </td>
      <td style="width: 16.6%; background: #fff1f0; border: 1px solid #ffa39e; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #ff4d4f;">{total_safety}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Safety Issues</div>
      </td>
      <td style="width: 16.6%; background: #f9f0ff; border: 1px solid #d3adf7; border-radius: 6px; padding: 10px 12px; text-align: center;">
        <div style="font-size: 22px; font-weight: 700; color: #722ed1;">{total_photos}</div>
        <div style="font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Photos</div>
      </td>
    </tr>
  </table>

  <!-- Weather Strip -->
  <table style="width: 100%; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 6px; padding: 8px 12px; margin-bottom: 14px; border-collapse: collapse;">
    <tr>
      <td style="width: 25%; padding: 6px 10px; border: none;">
        <span style="font-size: 9px; color: #999; text-transform: uppercase;">Weather</span><br/>
        <span style="font-size: 13px; font-weight: 600; color: #333;">{esc(weather_dominant) or 'N/A'}</span>
      </td>
      <td style="width: 25%; padding: 6px 10px; border: none;">
        <span style="font-size: 9px; color: #999; text-transform: uppercase;">Avg Temperature</span><br/>
        <span style="font-size: 13px; font-weight: 600; color: #333;">{avg_temp}&deg;F</span>
      </td>
      <td style="width: 25%; padding: 6px 10px; border: none;">
        <span style="font-size: 9px; color: #999; text-transform: uppercase;">Avg Humidity</span><br/>
        <span style="font-size: 13px; font-weight: 600; color: #333;">{avg_humidity}%</span>
      </td>
      <td style="width: 25%; padding: 6px 10px; border: none;">
        <span style="font-size: 9px; color: #999; text-transform: uppercase;">Avg Wind</span><br/>
        <span style="font-size: 13px; font-weight: 600; color: #333;">{avg_wind} mph</span>
      </td>
    </tr>
  </table>

  <!-- Charts Row: Activity Donut + Temperature Bars -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 14px;">
    <tr>
      <td style="width: 45%; vertical-align: top; padding-right: 12px;">
        <div style="border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px;">
          <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 8px;">Activity Distribution</div>
          {donut_svg}
        </div>
      </td>
      <td style="width: 55%; vertical-align: top;">
        <div style="border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px;">
          <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 8px;">Temperature &amp; Conditions</div>
          {temp_svg}
        </div>
      </td>
    </tr>
  </table>

  <!-- Inspection Results Bar -->
  {inspection_bar}

  <!-- Quick Summary Table -->
  <table style="width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 10px;">
    <tr style="background: #fafafa;">
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8; font-weight: 600; width: 50%;">Project</td>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8;">{esc(project.name)}</td>
    </tr>
    <tr>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8; font-weight: 600;">Report Date</td>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8;">{log.date.strftime('%B %d, %Y') if log.date else ''}</td>
    </tr>
    <tr style="background: #fafafa;">
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8; font-weight: 600;">Location</td>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8;">{esc(project.city or '')} {esc(project.state or '')}</td>
    </tr>
    <tr>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8; font-weight: 600;">Status</td>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8;">{esc(str(project.status).replace("_", " ").title() if project.status else "")}</td>
    </tr>
    <tr style="background: #fafafa;">
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8; font-weight: 600;">Total Entities Logged</td>
      <td style="padding: 5px 8px; border: 1px solid #e8e8e8;">{activity_total} items across {sum(1 for a in activities if a[1] > 0)} categories</td>
    </tr>
  </table>
</div>
'''
    return html


def _build_donut_svg(activities, total):
    """Build an inline SVG donut chart for activity distribution."""
    if total == 0:
        return '<div style="text-align:center;color:#999;padding:20px;">No activities recorded</div>'

    cx, cy, r = 90, 90, 70
    inner_r = 45
    svg_parts = [f'<svg viewBox="0 0 280 180" width="280" height="180" xmlns="http://www.w3.org/2000/svg">']

    # Draw arcs
    import math
    start_angle = -90  # Start from top
    for name, count, color in activities:
        if count == 0:
            continue
        pct = count / total
        end_angle = start_angle + pct * 360

        # Convert to radians
        s_rad = math.radians(start_angle)
        e_rad = math.radians(end_angle)

        # Outer arc points
        x1 = cx + r * math.cos(s_rad)
        y1 = cy + r * math.sin(s_rad)
        x2 = cx + r * math.cos(e_rad)
        y2 = cy + r * math.sin(e_rad)

        # Inner arc points
        x3 = cx + inner_r * math.cos(e_rad)
        y3 = cy + inner_r * math.sin(e_rad)
        x4 = cx + inner_r * math.cos(s_rad)
        y4 = cy + inner_r * math.sin(s_rad)

        large_arc = 1 if pct > 0.5 else 0

        path = (
            f'M {x1:.1f},{y1:.1f} '
            f'A {r},{r} 0 {large_arc},1 {x2:.1f},{y2:.1f} '
            f'L {x3:.1f},{y3:.1f} '
            f'A {inner_r},{inner_r} 0 {large_arc},0 {x4:.1f},{y4:.1f} Z'
        )
        svg_parts.append(f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="1"/>')
        start_angle = end_angle

    # Center text
    svg_parts.append(f'<text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="18" font-weight="700" fill="#333">{total}</text>')
    svg_parts.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="8" fill="#999">TOTAL</text>')

    # Legend (right side)
    ly = 10
    for name, count, color in activities:
        if count == 0:
            continue
        svg_parts.append(f'<rect x="190" y="{ly}" width="10" height="10" rx="2" fill="{color}"/>')
        svg_parts.append(f'<text x="204" y="{ly + 9}" font-size="9" fill="#555">{name} ({count})</text>')
        ly += 16

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def _build_temp_bar_svg(forecast_lines, weather_code_labels):
    """Build inline SVG bar chart for hourly temperature."""
    if not forecast_lines:
        return '<div style="text-align:center;color:#999;padding:20px;">No forecast data</div>'

    w, h = 320, 140
    bar_w = 36
    gap = 6
    max_temp = max((f.temperature or 0) for f in forecast_lines) or 100
    min_temp = min((f.temperature or 0) for f in forecast_lines) or 0
    temp_range = max(max_temp - min_temp, 1)

    svg = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']

    # Baseline
    base_y = h - 25

    for i, f in enumerate(forecast_lines[:6]):
        x = 10 + i * (bar_w + gap)
        temp = f.temperature or 0
        bar_h = max(((temp - min_temp) / temp_range) * (base_y - 15), 4)
        y = base_y - bar_h

        # Bar color based on weather code
        code_colors = {1: "#87CEEB", 2: "#B0C4DE", 3: "#4682B4", 4: "#2F4F8F", 5: "#1a1a4e"}
        color = code_colors.get(f.weather_code, "#87CEEB")

        svg.append(f'<rect x="{x}" y="{y:.0f}" width="{bar_w}" height="{bar_h:.0f}" rx="3" fill="{color}"/>')

        # Temperature label on bar
        svg.append(f'<text x="{x + bar_w/2}" y="{y - 3:.0f}" text-anchor="middle" font-size="9" font-weight="600" fill="#333">{temp:.0f}°</text>')

        # Time label below
        interval = str(f.time_interval or "")
        label = ""
        if "T" in interval:
            hour = int(interval.split("T")[1].split(":")[0])
            label = f"{hour}:00" if hour < 13 else f"{hour-12} PM"
            if hour < 12:
                label = f"{hour} AM"
            elif hour == 12:
                label = "12 PM"
        svg.append(f'<text x="{x + bar_w/2}" y="{base_y + 12}" text-anchor="middle" font-size="8" fill="#888">{label}</text>')

        # Weather icon text below time
        code_label = weather_code_labels.get(f.weather_code, "")
        svg.append(f'<text x="{x + bar_w/2}" y="{base_y + 22}" text-anchor="middle" font-size="7" fill="#aaa">{code_label}</text>')

    # Baseline
    svg.append(f'<line x1="5" y1="{base_y}" x2="{w-5}" y2="{base_y}" stroke="#ddd" stroke-width="1"/>')

    svg.append('</svg>')
    return '\n'.join(svg)


def _build_inspection_bar(pass_count, fail_count, other_count, total):
    """Build a horizontal stacked bar showing inspection results."""
    if total == 0:
        return ''

    pass_pct = (pass_count / total * 100) if total else 0
    fail_pct = (fail_count / total * 100) if total else 0
    other_pct = (other_count / total * 100) if total else 0

    return f'''
  <div style="border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px; margin-bottom: 10px;">
    <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 6px;">Inspection Results</div>
    <div style="display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #f5f5f5;">
      {'<div style="width:' + f'{pass_pct:.1f}' + '%;background:#52c41a;"></div>' if pass_count else ''}
      {'<div style="width:' + f'{fail_pct:.1f}' + '%;background:#ff4d4f;"></div>' if fail_count else ''}
      {'<div style="width:' + f'{other_pct:.1f}' + '%;background:#faad14;"></div>' if other_count else ''}
    </div>
    <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 9px; color: #666;">
      <span>&#9679; Pass: {pass_count} ({pass_pct:.0f}%)</span>
      <span style="color:#ff4d4f;">&#9679; Fail: {fail_count} ({fail_pct:.0f}%)</span>
      <span style="color:#faad14;">&#9679; Other: {other_count} ({other_pct:.0f}%)</span>
    </div>
  </div>
'''


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

    # ═══════════════════════════════════════════════════════════════════
    # OVERVIEW CANVAS — graphical dashboard page after title
    # ═══════════════════════════════════════════════════════════════════
    h.append(_render_overview_canvas(
        log=log, project=project,
        manpower_lines=manpower_lines, notes_lines=notes_lines,
        inspection_lines=inspection_lines, accident_lines=accident_lines,
        visitor_lines=visitor_lines, safety_lines=safety_lines,
        delay_lines=delay_lines, deficiency_lines=deficiency_lines,
        photo_lines=photo_lines, forecast_lines=forecast_lines,
        weather_code_labels=weather_code_labels, esc=esc,
    ))

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

def _render_project_dashboard(db, project, logs, esc):
    """Render a project-level executive dashboard page for the periodic report."""
    from sqlalchemy import func

    log_ids = [l.id for l in logs]
    if not log_ids:
        return ''

    # Aggregate metrics across all logs
    total_mp = db.query(func.sum(ManPower.number_of_workers)).filter(ManPower.dailylog_id.in_(log_ids)).scalar() or 0
    total_hours = db.query(func.sum(ManPower.total_hours)).filter(ManPower.dailylog_id.in_(log_ids)).scalar() or 0
    total_notes = db.query(func.count(Notes.id)).filter(Notes.dailylog_id.in_(log_ids)).scalar() or 0
    total_inspections = db.query(func.count(Inspection.id)).filter(Inspection.dailylog_id.in_(log_ids)).scalar() or 0
    total_visitors = db.query(func.count(Visitor.id)).filter(Visitor.dailylog_id.in_(log_ids)).scalar() or 0
    total_safety = db.query(func.count(SafetyViolation.id)).filter(SafetyViolation.dailylog_id.in_(log_ids)).scalar() or 0
    total_accidents = db.query(func.count(Accident.id)).filter(Accident.dailylog_id.in_(log_ids)).scalar() or 0
    total_delays = db.query(func.count(Delay.id)).filter(Delay.dailylog_id.in_(log_ids)).scalar() or 0
    total_deficiencies = db.query(func.count(Deficiency.id)).filter(Deficiency.dailylog_id.in_(log_ids)).scalar() or 0
    total_photos = db.query(func.count(Photo.id)).filter(Photo.dailylog_id.in_(log_ids)).scalar() or 0

    # Manpower trend by log date (for bar chart)
    mp_by_date = db.query(
        DailyActivityLog.date,
        func.sum(ManPower.number_of_workers),
        func.sum(ManPower.total_hours),
    ).join(ManPower, ManPower.dailylog_id == DailyActivityLog.id).filter(
        DailyActivityLog.id.in_(log_ids)
    ).group_by(DailyActivityLog.date).order_by(DailyActivityLog.date).all()

    # Build manpower trend SVG
    mp_trend_svg = _build_manpower_trend_svg(mp_by_date)

    # Activity breakdown for project
    activities = [
        ("Manpower Entries", db.query(func.count(ManPower.id)).filter(ManPower.dailylog_id.in_(log_ids)).scalar() or 0, "#1890ff"),
        ("Notes", total_notes, "#722ed1"),
        ("Inspections", total_inspections, "#13c2c2"),
        ("Visitors", total_visitors, "#52c41a"),
        ("Safety Issues", total_safety + total_accidents, "#ff4d4f"),
        ("Delays", total_delays, "#faad14"),
        ("Deficiencies", total_deficiencies, "#fa541c"),
        ("Photos", total_photos, "#2f54eb"),
    ]
    act_total = sum(a[1] for a in activities)
    donut_svg = _build_donut_svg(activities, act_total)

    # Inspection pass/fail across period
    pass_c = db.query(func.count(Inspection.id)).filter(
        Inspection.dailylog_id.in_(log_ids),
        func.lower(Inspection.result).in_(["pass", "passed"]),
    ).scalar() or 0
    fail_c = db.query(func.count(Inspection.id)).filter(
        Inspection.dailylog_id.in_(log_ids),
        func.lower(Inspection.result).in_(["fail", "failed"]),
    ).scalar() or 0
    other_c = total_inspections - pass_c - fail_c
    inspection_bar = _build_inspection_bar(pass_c, fail_c, other_c, total_inspections)

    date_range = ""
    if logs:
        d1 = min(l.date for l in logs if l.date)
        d2 = max(l.date for l in logs if l.date)
        date_range = f"{d1.strftime('%b %d')} — {d2.strftime('%b %d, %Y')}" if d1 and d2 else ""

    return f'''
<div class="page-break"></div>

<!-- ════════ PROJECT EXECUTIVE DASHBOARD ════════ -->
<div style="padding-top: 10px;">
  <h3 style="font-size: 16px; color: #1a1a1a; border-bottom: 2px solid #1890ff; padding-bottom: 4px; margin: 0 0 16px 0;">
    Project Executive Summary
  </h3>
  <p style="font-size: 11px; color: #666; margin: 0 0 14px 0;">
    {esc(project.name)} &mdash; {esc(date_range)} &mdash; {len(logs)} Daily Log(s)
  </p>

  <!-- KPI Cards -->
  <table style="width: 100%; border-collapse: separate; border-spacing: 6px 0; margin-bottom: 14px;">
    <tr>
      <td style="background: #f0f5ff; border: 1px solid #d6e4ff; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #1890ff;">{len(logs)}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Daily Logs</div>
      </td>
      <td style="background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #52c41a;">{int(total_mp)}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Workers</div>
      </td>
      <td style="background: #e6fffb; border: 1px solid #87e8de; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #13c2c2;">{int(total_hours):,}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Total Hours</div>
      </td>
      <td style="background: #fff7e6; border: 1px solid #ffe58f; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #faad14;">{total_inspections}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Inspections</div>
      </td>
      <td style="background: #fff1f0; border: 1px solid #ffa39e; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #ff4d4f;">{total_safety + total_accidents}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Safety Issues</div>
      </td>
      <td style="background: #f9f0ff; border: 1px solid #d3adf7; border-radius: 6px; padding: 10px; text-align: center;">
        <div style="font-size: 24px; font-weight: 700; color: #722ed1;">{total_photos}</div>
        <div style="font-size: 8px; color: #888; text-transform: uppercase;">Photos</div>
      </td>
    </tr>
  </table>

  <!-- Charts Row -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
    <tr>
      <td style="width: 40%; vertical-align: top; padding-right: 10px;">
        <div style="border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px;">
          <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 6px;">Activity Breakdown</div>
          {donut_svg}
        </div>
      </td>
      <td style="width: 60%; vertical-align: top;">
        <div style="border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px;">
          <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 6px;">Manpower Trend</div>
          {mp_trend_svg}
        </div>
      </td>
    </tr>
  </table>

  {inspection_bar}
</div>
'''


def _build_manpower_trend_svg(mp_by_date):
    """Build a bar chart SVG showing daily manpower over time."""
    if not mp_by_date:
        return '<div style="text-align:center;color:#999;padding:20px;">No manpower data</div>'

    import math
    w, h = 360, 130
    margin_left, margin_bottom = 35, 30
    chart_w = w - margin_left - 10
    chart_h = h - margin_bottom - 10

    max_workers = max(row[1] or 0 for row in mp_by_date) or 1
    n = len(mp_by_date)
    bar_w = max(3, min(20, (chart_w - n) / n))

    svg = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']

    # Y-axis labels
    for i in range(5):
        y = 5 + (chart_h / 4) * i
        val = int(max_workers - (max_workers / 4) * i)
        svg.append(f'<text x="{margin_left - 4}" y="{y + 3}" text-anchor="end" font-size="7" fill="#999">{val}</text>')
        svg.append(f'<line x1="{margin_left}" y1="{y}" x2="{w - 10}" y2="{y}" stroke="#f0f0f0" stroke-width="0.5"/>')

    # Bars
    for i, (dt, workers, hours) in enumerate(mp_by_date):
        x = margin_left + 2 + i * (bar_w + 1)
        workers = workers or 0
        bar_h = max(1, (workers / max_workers) * chart_h)
        y = 5 + chart_h - bar_h

        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="1" fill="#1890ff" opacity="0.8"/>')

        # Date label (show every Nth)
        if n <= 15 or i % max(1, n // 10) == 0:
            label = dt.strftime('%m/%d') if dt else ''
            svg.append(f'<text x="{x + bar_w/2:.1f}" y="{h - 5}" text-anchor="middle" font-size="6" fill="#999" transform="rotate(-45,{x + bar_w/2:.1f},{h - 5})">{label}</text>')

    # Baseline
    svg.append(f'<line x1="{margin_left}" y1="{5 + chart_h}" x2="{w - 10}" y2="{5 + chart_h}" stroke="#ddd" stroke-width="1"/>')

    svg.append('</svg>')
    return '\n'.join(svg)


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
    company_id = get_effective_company_id(current_user, db)

    project = db.query(Project).filter(Project.id == project_id, Project.company_id == company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch logs in date range
    log_q = db.query(DailyActivityLog).filter(
        DailyActivityLog.project_id == project_id,
        DailyActivityLog.company_id == company_id,
    )
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

    def esc(val):
        if val is None:
            return ''
        return str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    combined = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Project Report - {esc(project.name)}</title>
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
  <h2>{esc(project.name)}</h2>
  <p style="font-size:14px; color:#555;">{esc(project.ref_number)} | {esc(project.city or "")}, {esc(project.state or "")}</p>
  <p style="font-size:13px; color:#666;">Date Range: {esc(date_range_str)}</p>
  <p style="font-size:13px; color:#666;">{len(logs)} Daily Log(s)</p>
  <div class="meta">
    Generated on: {esc(now_str)}
  </div>
</div>

'''

    # ═══════ PROJECT EXECUTIVE DASHBOARD — after cover, before daily logs ═══════
    combined += _render_project_dashboard(db, project, logs, esc)

    for i, page in enumerate(all_pages):
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
