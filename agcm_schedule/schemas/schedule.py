"""Pydantic schemas for AGCM Schedule module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# SCHEDULE
# =============================================================================

class ScheduleCreate(BaseModel):
    name: str = Field(..., max_length=255)
    schedule_type: str = Field(default="baseline")
    project_id: int


class ScheduleUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    schedule_type: Optional[str] = None


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    version: int
    schedule_type: Optional[str] = None
    is_active: bool
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


# =============================================================================
# WBS
# =============================================================================

class WBSCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    parent_id: Optional[int] = None
    schedule_id: int
    project_id: int


class WBSUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None


class WBSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    parent_id: Optional[int] = None
    schedule_id: int
    project_id: int
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WBSTreeResponse(WBSResponse):
    children: List["WBSTreeResponse"] = []


# =============================================================================
# TASK
# =============================================================================

class TaskCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    task_type: str = Field(default="task")
    work_type: str = Field(default="work")
    status: str = Field(default="todo")
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    duration_days: int = 0
    wbs_id: Optional[int] = None
    schedule_id: int
    assigned_to: Optional[int] = None
    project_id: int


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    task_type: Optional[str] = None
    work_type: Optional[str] = None
    status: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    duration_days: Optional[int] = None
    progress: Optional[int] = None
    total_float: Optional[float] = None
    free_float: Optional[float] = None
    is_critical: Optional[bool] = None
    wbs_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    work_type: Optional[str] = None
    status: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    duration_days: int = 0
    progress: int = 0
    total_float: float = 0
    free_float: float = 0
    is_critical: bool = False
    wbs_id: Optional[int] = None
    schedule_id: int
    assigned_to: Optional[int] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


# =============================================================================
# DEPENDENCY
# =============================================================================

class DependencyCreate(BaseModel):
    predecessor_id: int
    successor_id: int
    dependency_type: str = Field(default="FS")
    lag_days: int = 0


class DependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predecessor_id: int
    successor_id: int
    dependency_type: Optional[str] = None
    lag_days: int = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# GANTT
# =============================================================================

class GanttDataResponse(BaseModel):
    tasks: List[TaskResponse] = []
    dependencies: List[DependencyResponse] = []
    wbs_items: List[WBSResponse] = []
