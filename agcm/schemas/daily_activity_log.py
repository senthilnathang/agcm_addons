"""Pydantic schemas for DailyActivityLog and child entities"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- DailyActivityLog ---

class DailyActivityLogCreate(BaseModel):
    date: date
    project_id: int


class DailyActivityLogUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: Optional[date] = None
    project_id: Optional[int] = None


class DailyActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    date: date
    project_id: int
    copy_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DailyActivityLogDetail(DailyActivityLogResponse):
    """Extended response with child counts"""
    weather_count: int = 0
    weather_forecast_count: int = 0
    manpower_count: int = 0
    notes_count: int = 0
    inspection_count: int = 0
    accident_count: int = 0
    visitor_count: int = 0
    safety_violation_count: int = 0
    delay_count: int = 0
    deficiency_count: int = 0
    photo_count: int = 0


# --- MakeLog (copy daily log) ---

class MakeLogRequest(BaseModel):
    """Request to copy a daily log with selective child entities"""
    source_log_id: int
    date: Optional[date] = None  # defaults to today
    copy_manpower: bool = False
    copy_safety: bool = False
    copy_observations: bool = False
    copy_inspections: bool = False
    copy_delays: bool = False


# --- ManPower ---

class ManPowerCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: Optional[str] = None
    location: Optional[str] = None
    number_of_workers: int = 0
    number_of_hours: float = 0.0
    partner_id: Optional[int] = None


class ManPowerUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    location: Optional[str] = None
    number_of_workers: Optional[int] = None
    number_of_hours: Optional[float] = None
    partner_id: Optional[int] = None


class ManPowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    number_of_workers: int = 0
    number_of_hours: float = 0.0
    total_hours: float = 0.0
    partner_id: Optional[int] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Notes ---

class NotesCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: Optional[str] = None
    note: Optional[str] = None
    description: Optional[str] = None
    issue: Optional[str] = None
    location: Optional[str] = None


class NotesUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    note: Optional[str] = None
    description: Optional[str] = None
    issue: Optional[str] = None
    location: Optional[str] = None


class NotesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: Optional[str] = None
    note: Optional[str] = None
    description: Optional[str] = None
    issue: Optional[str] = None
    location: Optional[str] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Inspection ---

class InspectionCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: Optional[str] = None
    inspection_type_id: Optional[int] = None
    result: str


class InspectionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    inspection_type_id: Optional[int] = None
    result: Optional[str] = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: Optional[str] = None
    inspection_type_id: Optional[int] = None
    result: str
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Accident ---

class AccidentCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str  # description
    accident_type_id: Optional[int] = None
    resolution: Optional[str] = None
    incident_time: Optional[datetime] = None
    location: Optional[str] = None
    safety_measure_precautions: bool = False


class AccidentUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    accident_type_id: Optional[int] = None
    resolution: Optional[str] = None
    incident_time: Optional[datetime] = None
    location: Optional[str] = None
    safety_measure_precautions: Optional[bool] = None


class AccidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    accident_type_id: Optional[int] = None
    resolution: Optional[str] = None
    incident_time: Optional[datetime] = None
    location: Optional[str] = None
    safety_measure_precautions: Optional[bool] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Visitor ---

class VisitorCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str
    reason: str
    visit_entry_time: datetime
    visit_exit_time: Optional[datetime] = None
    comments: Optional[str] = None
    user_id: Optional[int] = None


class VisitorUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    reason: Optional[str] = None
    visit_entry_time: Optional[datetime] = None
    visit_exit_time: Optional[datetime] = None
    comments: Optional[str] = None
    user_id: Optional[int] = None


class VisitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    reason: str
    visit_entry_time: datetime
    visit_exit_time: Optional[datetime] = None
    comments: Optional[str] = None
    user_id: Optional[int] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- SafetyViolation ---

class SafetyViolationCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str
    violation_notice: str
    violation_type_id: Optional[int] = None
    user_id: Optional[int] = None
    partner_id: Optional[int] = None


class SafetyViolationUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    violation_notice: Optional[str] = None
    violation_type_id: Optional[int] = None
    partner_id: Optional[int] = None


class SafetyViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    violation_notice: str
    violation_type_id: Optional[int] = None
    user_id: Optional[int] = None
    partner_id: Optional[int] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Delay ---

class DelayCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str
    reason: str
    delay: Optional[str] = None
    reported_by: Optional[str] = None
    partner_id: int


class DelayUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    reason: Optional[str] = None
    delay: Optional[str] = None
    reported_by: Optional[str] = None
    partner_id: Optional[int] = None


class DelayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    reason: str
    delay: Optional[str] = None
    reported_by: Optional[str] = None
    partner_id: int
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Deficiency ---

class DeficiencyCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str
    description: str


class DeficiencyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None


class DeficiencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: str
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- Photo ---

class PhotoCreate(BaseModel):
    dailylog_id: int
    project_id: Optional[int] = None
    name: str
    file_name: Optional[str] = None
    location: Optional[str] = None
    album: Optional[str] = None
    taken_on: Optional[datetime] = None


class PhotoUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    file_name: Optional[str] = None
    location: Optional[str] = None
    album: Optional[str] = None
    taken_on: Optional[datetime] = None


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    file_name: Optional[str] = None
    location: Optional[str] = None
    album: Optional[str] = None
    taken_on: Optional[datetime] = None
    dailylog_id: int
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


# --- WeatherForecast ---

class WeatherForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: Optional[date] = None
    time_interval: Optional[str] = None
    temperature: Optional[float] = None
    temperature_type: Optional[str] = None
    weather_code: Optional[int] = None
    humidity: Optional[float] = None
    wind: Optional[float] = None
    precipitation: Optional[float] = None
    dailylog_id: Optional[int] = None
    project_id: Optional[int] = None
