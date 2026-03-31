"""Pydantic schemas for Punch List Items"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PunchListItemCreate(BaseModel):
    project_id: int
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    location: Optional[str] = None
    trade: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    photo_before_url: Optional[str] = None
    notes: Optional[str] = None


class PunchListItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None
    trade: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    verified_date: Optional[date] = None
    verified_by: Optional[int] = None
    photo_before_url: Optional[str] = None
    photo_after_url: Optional[str] = None
    notes: Optional[str] = None


class PunchListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    project_id: int
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None
    trade: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    verified_date: Optional[date] = None
    verified_by: Optional[int] = None
    photo_before_url: Optional[str] = None
    photo_after_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
