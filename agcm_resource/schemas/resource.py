"""Pydantic schemas for Resource models (Worker, Equipment, Timesheet, EquipmentAssignment)"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# WORKER SCHEMAS
# =============================================================================

class WorkerBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field("active", max_length=20)
    skill_level: Optional[str] = Field(None, max_length=20)
    trade: Optional[str] = Field(None, max_length=100)
    hourly_rate: float = Field(0, ge=0, le=9999.99)
    overtime_rate: float = Field(0, ge=0, le=9999.99)
    certifications: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    user_id: Optional[int] = None
    is_subcontractor: bool = False
    notes: Optional[str] = None


class WorkerCreate(WorkerBase):
    pass


class WorkerUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    skill_level: Optional[str] = Field(None, max_length=20)
    trade: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[float] = Field(None, ge=0, le=9999.99)
    overtime_rate: Optional[float] = Field(None, ge=0, le=9999.99)
    certifications: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    user_id: Optional[int] = None
    is_subcontractor: Optional[bool] = None
    notes: Optional[str] = None


class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    skill_level: Optional[str] = None
    trade: Optional[str] = None
    hourly_rate: float = 0
    overtime_rate: float = 0
    certifications: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    hire_date: Optional[date] = None
    user_id: Optional[int] = None
    is_subcontractor: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# EQUIPMENT SCHEMAS
# =============================================================================

class EquipmentBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    equipment_type: str = Field(..., max_length=100)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    serial_number: Optional[str] = Field(None, max_length=100)
    license_plate: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field("available", max_length=20)
    ownership_type: str = Field("owned", max_length=50)
    daily_rate: float = Field(0, ge=0, le=99999.99)
    hourly_rate: float = Field(0, ge=0, le=99999.99)
    current_project_id: Optional[int] = None
    current_location: Optional[str] = Field(None, max_length=255)
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    equipment_type: Optional[str] = Field(None, max_length=100)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    serial_number: Optional[str] = Field(None, max_length=100)
    license_plate: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    ownership_type: Optional[str] = Field(None, max_length=50)
    daily_rate: Optional[float] = Field(None, ge=0, le=99999.99)
    hourly_rate: Optional[float] = Field(None, ge=0, le=99999.99)
    current_project_id: Optional[int] = None
    current_location: Optional[str] = Field(None, max_length=255)
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    equipment_type: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    serial_number: Optional[str] = None
    license_plate: Optional[str] = None
    status: Optional[str] = None
    ownership_type: str = "owned"
    daily_rate: float = 0
    hourly_rate: float = 0
    current_project_id: Optional[int] = None
    current_location: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# TIMESHEET SCHEMAS
# =============================================================================

class TimesheetBase(BaseModel):
    worker_id: int
    project_id: int
    date: date
    regular_hours: float = Field(0, ge=0, le=24)
    overtime_hours: float = Field(0, ge=0, le=24)
    double_time_hours: float = Field(0, ge=0, le=24)
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    task_description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class TimesheetCreate(TimesheetBase):
    pass


class TimesheetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    worker_id: Optional[int] = None
    project_id: Optional[int] = None
    date: Optional[date] = None
    regular_hours: Optional[float] = Field(None, ge=0, le=24)
    overtime_hours: Optional[float] = Field(None, ge=0, le=24)
    double_time_hours: Optional[float] = Field(None, ge=0, le=24)
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    task_description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class TimesheetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    worker_id: int
    project_id: int
    date: date
    regular_hours: float = 0
    overtime_hours: float = 0
    double_time_hours: float = 0
    total_hours: float = 0
    regular_cost: float = 0
    overtime_cost: float = 0
    total_cost: float = 0
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: Optional[str] = None
    approved_by: Optional[int] = None
    approved_date: Optional[date] = None
    task_description: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Joined fields for display
    worker_name: Optional[str] = None
    project_name: Optional[str] = None


# =============================================================================
# EQUIPMENT ASSIGNMENT SCHEMAS
# =============================================================================

class EquipmentAssignmentBase(BaseModel):
    equipment_id: int
    project_id: int
    assigned_date: date
    return_date: Optional[date] = None
    daily_rate: float = Field(0, ge=0, le=99999.99)
    total_days: int = Field(0, ge=0, le=9999)
    total_cost: float = Field(0, ge=0, le=9999999.99)
    notes: Optional[str] = None


class EquipmentAssignmentCreate(EquipmentAssignmentBase):
    pass


class EquipmentAssignmentUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    equipment_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_date: Optional[date] = None
    return_date: Optional[date] = None
    daily_rate: Optional[float] = Field(None, ge=0, le=99999.99)
    total_days: Optional[int] = Field(None, ge=0, le=9999)
    total_cost: Optional[float] = Field(None, ge=0, le=9999999.99)
    notes: Optional[str] = None


class EquipmentAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    equipment_id: int
    project_id: int
    assigned_date: date
    return_date: Optional[date] = None
    daily_rate: float = 0
    total_days: int = 0
    total_cost: float = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Joined fields for display
    equipment_name: Optional[str] = None
    project_name: Optional[str] = None
