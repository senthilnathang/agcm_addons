"""Pydantic schemas for AGCM Progress module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# MILESTONES
# =============================================================================

class MilestoneCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    is_completed: bool = False
    project_id: int


class MilestoneUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    is_completed: Optional[bool] = None


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    is_completed: bool = False
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ISSUES
# =============================================================================

class IssueCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    severity: str = "minor"
    status: str = "open"
    priority: str = "medium"
    location: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    reported_by: Optional[int] = None
    project_id: int


class IssueUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    reported_by: Optional[int] = None


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None
    due_date: Optional[date] = None
    resolved_date: Optional[date] = None
    assigned_to: Optional[int] = None
    reported_by: Optional[int] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ESTIMATION
# =============================================================================

class EstimationItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    cost_type: str = "material"
    quantity: float = 0
    unit: Optional[str] = None
    unit_cost: float = 0
    total_cost: float = 0
    status: str = "incomplete"
    parent_id: Optional[int] = None
    project_id: int


class EstimationItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    cost_type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    status: Optional[str] = None
    parent_id: Optional[int] = None


class EstimationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    cost_type: Optional[str] = None
    quantity: float = 0
    unit: Optional[str] = None
    unit_cost: float = 0
    total_cost: float = 0
    status: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EstimationTreeResponse(EstimationItemResponse):
    children: List["EstimationTreeResponse"] = []
    rollup_total: float = 0


# =============================================================================
# S-CURVE
# =============================================================================

class SCurveDataCreate(BaseModel):
    project_id: int
    date: date
    planned_physical_pct: float = 0
    actual_physical_pct: float = 0
    revised_physical_pct: float = 0
    planned_financial_pct: float = 0
    actual_financial_pct: float = 0
    manpower_progress_pct: float = 0
    machinery_progress_pct: float = 0
    schedule_days_ahead: int = 0


class SCurveDataUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: Optional[date] = None
    planned_physical_pct: Optional[float] = None
    actual_physical_pct: Optional[float] = None
    revised_physical_pct: Optional[float] = None
    planned_financial_pct: Optional[float] = None
    actual_financial_pct: Optional[float] = None
    manpower_progress_pct: Optional[float] = None
    machinery_progress_pct: Optional[float] = None
    schedule_days_ahead: Optional[int] = None


class SCurveDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    date: date
    planned_physical_pct: float = 0
    actual_physical_pct: float = 0
    revised_physical_pct: float = 0
    planned_financial_pct: float = 0
    actual_financial_pct: float = 0
    manpower_progress_pct: float = 0
    machinery_progress_pct: float = 0
    schedule_days_ahead: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SCurveChartData(BaseModel):
    items: List[SCurveDataResponse] = []


# =============================================================================
# PROJECT IMAGES
# =============================================================================

class ProjectImageCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    tags: Optional[str] = None
    display_order: int = 0
    taken_on: Optional[date] = None
    project_id: int


class ProjectImageUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    display_order: Optional[int] = None
    taken_on: Optional[date] = None


class ProjectImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    tags: Optional[str] = None
    document_id: Optional[int] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    display_order: int = 0
    taken_on: Optional[date] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
