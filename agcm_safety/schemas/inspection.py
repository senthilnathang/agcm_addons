"""Pydantic schemas for Inspections"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Inspection Items ---

class InspectionItemCreate(BaseModel):
    description: str = Field(..., max_length=500)
    result: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    display_order: Optional[int] = 0


class InspectionItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = None
    result: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    display_order: Optional[int] = None


class InspectionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    description: str
    result: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    display_order: int = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Inspection ---

class InspectionCreate(BaseModel):
    project_id: int
    template_id: Optional[int] = None
    inspector_name: str = Field(..., max_length=255)
    inspector_company: Optional[str] = None
    inspection_type: Optional[str] = None
    scheduled_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[InspectionItemCreate]] = []


class InspectionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    inspector_name: Optional[str] = None
    inspector_company: Optional[str] = None
    inspection_type: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    overall_result: Optional[str] = None
    items: Optional[List[InspectionItemCreate]] = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    project_id: int
    template_id: Optional[int] = None
    inspector_name: str
    inspector_company: Optional[str] = None
    inspection_type: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    overall_result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InspectionDetail(InspectionResponse):
    """Extended response with checklist items."""
    items: List[InspectionItemResponse] = []
