"""Weather API endpoints — forecast fetch + manual weather CRUD"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id
from addons.agcm.services.weather_service import WeatherService

router = APIRouter()


def _get_service(db, current_user):
    company_id = get_effective_company_id(current_user, db)
    return WeatherService(db=db, company_id=company_id, user_id=current_user.id)


# --- Forecast (auto-fetch from weather.gov) ---

@router.post("/weather/fetch-forecast", response_model=None)
async def fetch_weather_forecast(
    project_id: int = Query(...),
    log_date: date = Query(...),
    dailylog_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch weather forecast from weather.gov for a project location and date.
    Returns existing data if already fetched."""
    svc = _get_service(db, current_user)
    forecasts = svc.fetch_forecast(project_id, log_date, dailylog_id)
    return {"items": forecasts, "total": len(forecasts)}


@router.get("/weather/forecast", response_model=None)
async def get_weather_forecast(
    dailylog_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get stored weather forecast for a daily log."""
    svc = _get_service(db, current_user)
    forecasts = svc._get_forecasts(dailylog_id)
    return {"items": forecasts, "total": len(forecasts)}


# --- Manual weather entries (observed conditions) ---

class ManualWeatherCreate(BaseModel):
    temperature: float = 0
    temperature_type: str = "F"
    climate_type: str = "clear"
    humidity: float = 0
    wind: float = 0
    precipitation: float = 0
    rain: bool = False
    rain_fall: float = 0


@router.get("/weather/manual", response_model=None)
async def list_manual_weather(
    dailylog_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List manual weather observations for a daily log."""
    svc = _get_service(db, current_user)
    items = svc.list_manual_weather(dailylog_id)
    return {"items": items, "total": len(items)}


@router.post("/weather/manual", response_model=None, status_code=201)
async def create_manual_weather(
    dailylog_id: int = Query(...),
    data: ManualWeatherCreate = ...,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a manual weather observation to a daily log."""
    from addons.agcm.models.daily_activity_log import DailyActivityLog
    log = db.query(DailyActivityLog).filter(DailyActivityLog.id == dailylog_id).first()
    svc = _get_service(db, current_user)
    create_data = data.model_dump()
    if log:
        create_data["date"] = log.date
        create_data["project_id"] = log.project_id
    w = svc.create_manual_weather(dailylog_id, create_data)
    return {
        "id": w.id,
        "sequence_name": w.sequence_name,
        "temperature": w.temperature,
        "climate_type": w.climate_type,
    }
