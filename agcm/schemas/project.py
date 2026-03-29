"""Pydantic schemas for Project"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Project ---

class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    ref_number: str = Field(..., max_length=100)
    start_date: date
    end_date: date
    trade_id: Optional[int] = None
    owner_id: int
    status: Optional[str] = "new"
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    agcm_office: Optional[str] = None


class ProjectCreate(ProjectBase):
    user_ids: Optional[List[int]] = []
    partner_ids: Optional[List[int]] = []


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    ref_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    trade_id: Optional[int] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    agcm_office: Optional[str] = None
    user_ids: Optional[List[int]] = None
    partner_ids: Optional[List[int]] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    ref_number: str
    start_date: date
    end_date: date
    status: Optional[str] = None
    trade_id: Optional[int] = None
    owner_id: Optional[int] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    project_latitude: Optional[float] = None
    project_longitude: Optional[float] = None
    agcm_office: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectDetail(ProjectResponse):
    """Extended response with related data"""
    user_ids: List[int] = []
    partner_ids: List[int] = []
    daily_log_count: int = 0
