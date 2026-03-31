"""Pydantic schemas for Incident Reports"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IncidentReportCreate(BaseModel):
    project_id: int
    title: str = Field(..., max_length=500)
    description: str = Field(..., max_length=5000)
    severity: str = Field(..., max_length=50)
    incident_date: date
    incident_time: Optional[str] = Field(None, max_length=10)
    location: Optional[str] = Field(None, max_length=255)
    injured_party: Optional[str] = Field(None, max_length=255)
    injury_description: Optional[str] = Field(None, max_length=5000)
    witness_names: Optional[str] = Field(None, max_length=1000)
    osha_recordable: Optional[bool] = False
    photo_urls: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=5000)


class IncidentReportUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    severity: Optional[str] = Field(None, max_length=50)
    incident_date: Optional[date] = None
    incident_time: Optional[str] = Field(None, max_length=10)
    location: Optional[str] = Field(None, max_length=255)
    injured_party: Optional[str] = Field(None, max_length=255)
    injury_description: Optional[str] = Field(None, max_length=5000)
    witness_names: Optional[str] = Field(None, max_length=1000)
    osha_recordable: Optional[bool] = None
    photo_urls: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=5000)


class IncidentReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    project_id: int
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    incident_date: Optional[date] = None
    incident_time: Optional[str] = None
    location: Optional[str] = None
    injured_party: Optional[str] = None
    injury_description: Optional[str] = None
    witness_names: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    reported_by: Optional[int] = None
    investigated_by: Optional[int] = None
    investigation_date: Optional[date] = None
    closed_date: Optional[date] = None
    osha_recordable: bool = False
    days_lost: int = 0
    photo_urls: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
