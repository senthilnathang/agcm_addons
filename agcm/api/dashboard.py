"""Dashboard analytics API — pre-aggregated data for charts and KPIs"""

from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, extract, case, and_
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

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
from addons.agcm.models.weather import Weather, WeatherForecast

router = APIRouter()


def _date_filters(model_date_col, date_from, date_to):
    """Build date range filter clauses."""
    filters = []
    if date_from:
        filters.append(model_date_col >= date_from)
    if date_to:
        filters.append(model_date_col <= date_to)
    return filters


# =========================================================================
# 1. OVERVIEW DASHBOARD — all projects
# =========================================================================

@router.get("/dashboard/overview", response_model=None)
async def dashboard_overview(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Overall executive dashboard with KPIs and chart data across all projects."""
    cid = get_effective_company_id(current_user, db)

    # Base log query with date filters — use subquery to avoid unbounded IN clause
    log_q = db.query(DailyActivityLog.id).filter(DailyActivityLog.company_id == cid)
    for f in _date_filters(DailyActivityLog.date, date_from, date_to):
        log_q = log_q.filter(f)
    log_subq = log_q.subquery()
    log_id_q = db.query(log_subq.c.id)

    total_logs = log_id_q.count()

    # --- KPIs ---
    total_projects = db.query(func.count(Project.id)).filter(
        Project.company_id == cid, Project.is_deleted == False
    ).scalar() or 0

    active_projects = db.query(func.count(Project.id)).filter(
        Project.company_id == cid, Project.is_deleted == False, Project.status == "inprogress"
    ).scalar() or 0

    mp_stats = db.query(
        func.coalesce(func.sum(ManPower.total_hours), 0),
        func.coalesce(func.sum(ManPower.number_of_workers), 0),
    ).filter(ManPower.dailylog_id.in_(log_id_q)).first() or (0, 0)

    total_safety = (
        (db.query(func.count(Accident.id)).filter(Accident.dailylog_id.in_(log_id_q)).scalar() or 0) +
        (db.query(func.count(SafetyViolation.id)).filter(SafetyViolation.dailylog_id.in_(log_id_q)).scalar() or 0)
    )

    total_inspections = db.query(func.count(Inspection.id)).filter(
        Inspection.dailylog_id.in_(log_id_q)
    ).scalar() or 0

    total_photos = db.query(func.count(Photo.id)).filter(
        Photo.dailylog_id.in_(log_id_q)
    ).scalar() or 0

    total_visitors = db.query(func.count(Visitor.id)).filter(
        Visitor.dailylog_id.in_(log_id_q)
    ).scalar() or 0

    # --- Project Status Donut ---
    status_rows = db.query(Project.status, func.count(Project.id)).filter(
        Project.company_id == cid, Project.is_deleted == False
    ).group_by(Project.status).all()

    status_labels = {"new": "New", "inprogress": "In Progress", "completed": "Completed"}
    project_status_chart = [
        {"name": status_labels.get(s, s), "value": c} for s, c in status_rows
    ]

    # --- Manpower by Project (bar chart) ---
    mp_by_proj = db.query(
        Project.name, func.coalesce(func.sum(ManPower.total_hours), 0)
    ).join(DailyActivityLog, DailyActivityLog.project_id == Project.id
    ).join(ManPower, ManPower.dailylog_id == DailyActivityLog.id
    ).filter(Project.company_id == cid)
    for f in _date_filters(DailyActivityLog.date, date_from, date_to):
        mp_by_proj = mp_by_proj.filter(f)
    mp_by_proj = mp_by_proj.group_by(Project.name).order_by(func.sum(ManPower.total_hours).desc()).limit(10).all()

    manpower_by_project = [{"name": n, "value": round(float(v), 1)} for n, v in mp_by_proj]

    # --- Safety Trend (line chart by month) ---
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    accident_by_month = defaultdict(int)
    violation_by_month = defaultdict(int)

    acc_rows = db.query(
        extract('month', DailyActivityLog.date).label('m'), func.count(Accident.id)
    ).join(DailyActivityLog, Accident.dailylog_id == DailyActivityLog.id
    ).filter(Accident.dailylog_id.in_(log_id_q)
    ).group_by('m').all()
    for m, c in acc_rows:
        accident_by_month[int(m)] = c

    viol_rows = db.query(
        extract('month', DailyActivityLog.date).label('m'), func.count(SafetyViolation.id)
    ).join(DailyActivityLog, SafetyViolation.dailylog_id == DailyActivityLog.id
    ).filter(SafetyViolation.dailylog_id.in_(log_id_q)
    ).group_by('m').all()
    for m, c in viol_rows:
        violation_by_month[int(m)] = c

    active_months = sorted(set(list(accident_by_month.keys()) + list(violation_by_month.keys())))
    if not active_months:
        active_months = [1, 2, 3]

    safety_trend = {
        "categories": [months[m - 1] for m in active_months],
        "series": [
            {"name": "Accidents", "data": [accident_by_month.get(m, 0) for m in active_months]},
            {"name": "Safety Violations", "data": [violation_by_month.get(m, 0) for m in active_months]},
        ],
    }

    # --- Activity by Type (pie chart) ---
    activity_counts = []
    for label, model in [
        ("Manpower", ManPower), ("Notes", Notes), ("Inspections", Inspection),
        ("Visitors", Visitor), ("Safety", SafetyViolation), ("Delays", Delay),
        ("Deficiencies", Deficiency), ("Accidents", Accident), ("Photos", Photo),
    ]:
        c = db.query(func.count(model.id)).filter(model.dailylog_id.in_(log_id_q)).scalar() or 0
        if c > 0:
            activity_counts.append({"name": label, "value": c})

    # --- Weather Summary ---
    weather_summary = {}
    wf_stats = db.query(
        func.avg(WeatherForecast.temperature),
        func.avg(WeatherForecast.humidity),
        func.avg(WeatherForecast.wind),
    ).filter(WeatherForecast.dailylog_id.in_(log_id_q)).first()
    if wf_stats and wf_stats[0]:
        weather_summary = {
            "avg_temperature": round(float(wf_stats[0] or 0), 1),
            "avg_humidity": round(float(wf_stats[1] or 0), 1),
            "avg_wind": round(float(wf_stats[2] or 0), 1),
        }

    # --- Recent Logs ---
    recent = db.query(
        DailyActivityLog.id, DailyActivityLog.sequence_name,
        DailyActivityLog.date, DailyActivityLog.project_id,
        Project.name.label("project_name"),
    ).join(Project, DailyActivityLog.project_id == Project.id
    ).filter(DailyActivityLog.company_id == cid
    ).order_by(DailyActivityLog.date.desc()).limit(10).all()

    recent_logs = [
        {"id": r.id, "sequence_name": r.sequence_name, "date": str(r.date),
         "project_id": r.project_id, "project_name": r.project_name}
        for r in recent
    ]

    return {
        "kpis": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_daily_logs": total_logs,
            "total_manpower_hours": round(float(mp_stats[0]), 1),
            "total_workers": int(mp_stats[1]),
            "total_safety_incidents": total_safety,
            "total_inspections": total_inspections,
            "total_photos": total_photos,
            "total_visitors": total_visitors,
        },
        "project_status_chart": project_status_chart,
        "manpower_by_project": manpower_by_project,
        "safety_trend": safety_trend,
        "activity_by_type": activity_counts,
        "weather_summary": weather_summary,
        "recent_logs": recent_logs,
    }


# =========================================================================
# 2. PROJECT DASHBOARD — single project deep-dive
# =========================================================================

@router.get("/dashboard/project/{project_id}", response_model=None)
async def dashboard_project(
    project_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Project-level analytics with trends and breakdowns."""
    cid = get_effective_company_id(current_user, db)
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == cid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    log_q = db.query(DailyActivityLog).filter(DailyActivityLog.project_id == project_id)
    for f in _date_filters(DailyActivityLog.date, date_from, date_to):
        log_q = log_q.filter(f)
    logs = log_q.order_by(DailyActivityLog.date).all()

    # Use subquery for child entity queries to avoid unbounded IN clause
    log_id_subq = db.query(DailyActivityLog.id).filter(
        DailyActivityLog.project_id == project_id
    )
    for f in _date_filters(DailyActivityLog.date, date_from, date_to):
        log_id_subq = log_id_subq.filter(f)
    log_subq = log_id_subq.subquery()
    log_id_q = db.query(log_subq.c.id)

    # KPIs
    mp_stats = db.query(
        func.coalesce(func.sum(ManPower.total_hours), 0),
        func.coalesce(func.sum(ManPower.number_of_workers), 0),
    ).filter(ManPower.dailylog_id.in_(log_id_q)).first() or (0, 0)

    accidents_count = db.query(func.count(Accident.id)).filter(Accident.dailylog_id.in_(log_id_q)).scalar() or 0
    violations_count = db.query(func.count(SafetyViolation.id)).filter(SafetyViolation.dailylog_id.in_(log_id_q)).scalar() or 0
    delays_count = db.query(func.count(Delay.id)).filter(Delay.dailylog_id.in_(log_id_q)).scalar() or 0
    deficiencies_count = db.query(func.count(Deficiency.id)).filter(Deficiency.dailylog_id.in_(log_id_q)).scalar() or 0
    inspections_count = db.query(func.count(Inspection.id)).filter(Inspection.dailylog_id.in_(log_id_q)).scalar() or 0
    photos_count = db.query(func.count(Photo.id)).filter(Photo.dailylog_id.in_(log_id_q)).scalar() or 0

    # Daily log activity timeline (line chart)
    log_dates = [str(l.date) for l in logs]
    # Group by week for manpower trend
    weekly_mp = defaultdict(float)
    weekly_rows = db.query(
        extract('week', DailyActivityLog.date).label('w'),
        func.sum(ManPower.total_hours),
    ).join(DailyActivityLog, ManPower.dailylog_id == DailyActivityLog.id
    ).filter(ManPower.dailylog_id.in_(log_id_q)
    ).group_by('w').order_by('w').all()
    for w, h in weekly_rows:
        weekly_mp[f"W{int(w)}"] = round(float(h), 1)

    manpower_weekly = [{"name": k, "value": v} for k, v in weekly_mp.items()]

    # Inspection pass/fail donut
    insp_rows = db.query(Inspection.result, func.count(Inspection.id)).filter(
        Inspection.dailylog_id.in_(log_id_q)
    ).group_by(Inspection.result).all()
    inspection_results = [{"name": r or "Unknown", "value": c} for r, c in insp_rows]

    # Severity funnel
    severity_funnel = [
        {"name": "Deficiencies", "value": deficiencies_count or 0},
        {"name": "Delays", "value": delays_count or 0},
        {"name": "Safety Violations", "value": violations_count or 0},
        {"name": "Accidents", "value": accidents_count or 0},
    ]

    # Weather summary
    weather_summary = {}
    wf = db.query(
        func.avg(WeatherForecast.temperature),
        func.avg(WeatherForecast.humidity),
        func.count(case((WeatherForecast.weather_code >= 3, 1))),
    ).filter(WeatherForecast.dailylog_id.in_(log_id_q)).first()
    if wf and wf[0]:
        weather_summary = {
            "avg_temperature": round(float(wf[0] or 0), 1),
            "avg_humidity": round(float(wf[1] or 0), 1),
            "rainy_readings": int(wf[2] or 0),
        }

    return {
        "project": {
            "id": project.id, "name": project.name, "ref_number": project.ref_number,
            "status": project.status, "start_date": str(project.start_date),
            "end_date": str(project.end_date), "city": project.city, "state": project.state,
        },
        "kpis": {
            "total_logs": len(logs),
            "total_manpower_hours": round(float(mp_stats[0]), 1),
            "avg_workers_per_day": round(float(mp_stats[1]) / max(len(logs), 1), 1),
            "safety_incidents": (accidents_count or 0) + (violations_count or 0),
            "inspections": inspections_count or 0,
            "photos": photos_count or 0,
        },
        "log_timeline": {
            "categories": log_dates[-30:],  # last 30 entries
            "series": [{"name": "Daily Logs", "data": [1] * min(len(log_dates), 30)}],
        },
        "manpower_weekly": manpower_weekly,
        "inspection_results": inspection_results,
        "severity_funnel": severity_funnel,
        "weather_summary": weather_summary,
    }


# =========================================================================
# 3. DAILY LOG DASHBOARD — single log breakdown
# =========================================================================

@router.get("/dashboard/dailylog/{log_id}", response_model=None)
async def dashboard_dailylog(
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Daily log analytics — full breakdown of a single day's activities."""
    cid = get_effective_company_id(current_user, db)
    log = db.query(DailyActivityLog).filter(
        DailyActivityLog.id == log_id, DailyActivityLog.company_id == cid
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    project = db.query(Project).filter(Project.id == log.project_id).first()

    # Count all child entities
    counts = {}
    for label, model in [
        ("Manpower", ManPower), ("Notes", Notes), ("Inspections", Inspection),
        ("Accidents", Accident), ("Visitors", Visitor), ("Safety Obs.", SafetyViolation),
        ("Delays", Delay), ("Deficiencies", Deficiency), ("Photos", Photo),
    ]:
        counts[label] = db.query(func.count(model.id)).filter(model.dailylog_id == log_id).scalar() or 0

    activity_donut = [{"name": k, "value": v} for k, v in counts.items() if v > 0]

    # Manpower details
    mp_rows = db.query(ManPower).filter(ManPower.dailylog_id == log_id).all()
    manpower_data = [
        {"name": m.name or "N/A", "location": m.location or "", "workers": m.number_of_workers,
         "hours": m.number_of_hours, "total_hours": m.total_hours}
        for m in mp_rows
    ]
    manpower_by_location = defaultdict(float)
    for m in mp_rows:
        manpower_by_location[m.location or "Other"] += m.total_hours
    mp_location_chart = [{"name": k, "value": round(v, 1)} for k, v in manpower_by_location.items()]

    # Weather forecast
    forecasts = db.query(WeatherForecast).filter(
        WeatherForecast.dailylog_id == log_id
    ).order_by(WeatherForecast.time_interval).all()

    weather_code_labels = {1: "Clear", 2: "Cloudy", 3: "Light Rain", 4: "Heavy Rain", 5: "Thunder"}
    weather_strip = [
        {"time": f.time_interval, "temperature": f.temperature, "humidity": f.humidity,
         "wind": f.wind, "weather_code": f.weather_code,
         "label": weather_code_labels.get(f.weather_code, "N/A")}
        for f in forecasts
    ]

    # Inspection results breakdown
    insp_rows = db.query(Inspection.result, func.count(Inspection.id)).filter(
        Inspection.dailylog_id == log_id
    ).group_by(Inspection.result).all()
    inspection_chart = [{"name": r or "Unknown", "value": c} for r, c in insp_rows]

    # Safety details
    safety_items = db.query(SafetyViolation).filter(SafetyViolation.dailylog_id == log_id).all()
    safety_list = [{"name": s.name, "notice": s.violation_notice} for s in safety_items]

    return {
        "log": {
            "id": log.id, "sequence_name": log.sequence_name, "date": str(log.date),
            "project_id": log.project_id,
            "project_name": project.name if project else "Unknown",
        },
        "kpis": counts,
        "activity_donut": activity_donut,
        "manpower_data": manpower_data,
        "manpower_by_location": mp_location_chart,
        "weather_strip": weather_strip,
        "inspection_chart": inspection_chart,
        "safety_list": safety_list,
    }
