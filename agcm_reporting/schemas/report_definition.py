"""Pydantic schemas for ReportDefinition and ReportSchedule"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- ReportSchedule ---

class ReportScheduleBase(BaseModel):
    schedule_type: str = Field(..., max_length=20)  # daily, weekly, monthly
    recipients: Optional[str] = Field(None, max_length=5000)  # JSON array of emails
    is_active: bool = True
    format: str = Field("pdf", max_length=10)


class ReportScheduleCreate(ReportScheduleBase):
    pass


class ReportScheduleUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schedule_type: Optional[str] = Field(None, max_length=20)
    recipients: Optional[str] = Field(None, max_length=5000)
    next_run: Optional[datetime] = None
    is_active: Optional[bool] = None
    format: Optional[str] = Field(None, max_length=10)


class ReportScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    company_id: int
    schedule_type: str
    recipients: Optional[str] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    is_active: bool = True
    format: Optional[str] = "pdf"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- ReportDefinition ---

class ReportDefinitionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    report_type: str = Field("custom", max_length=50)
    data_source: str = Field(..., max_length=100)
    columns: Optional[str] = Field(None, max_length=10000)
    filters: Optional[str] = Field(None, max_length=5000)
    sort_by: Optional[str] = Field(None, max_length=100)
    sort_order: str = Field("desc", max_length=10)
    group_by: Optional[str] = Field(None, max_length=100)
    is_shared: bool = True


class ReportDefinitionCreate(ReportDefinitionBase):
    pass


class ReportDefinitionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    report_type: Optional[str] = Field(None, max_length=50)
    data_source: Optional[str] = Field(None, max_length=100)
    columns: Optional[str] = Field(None, max_length=10000)
    filters: Optional[str] = Field(None, max_length=5000)
    sort_by: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[str] = Field(None, max_length=10)
    group_by: Optional[str] = Field(None, max_length=100)
    is_shared: Optional[bool] = None


class ReportDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    report_type: Optional[str] = None
    data_source: str
    columns: Optional[str] = None
    filters: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    group_by: Optional[str] = None
    is_system: bool = False
    is_shared: bool = True
    created_by: Optional[int] = None
    schedules: List[ReportScheduleResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
