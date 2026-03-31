"""Pydantic schemas for T&M Tickets"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# T&M TICKET LINE
# =============================================================================

class TMTicketLineCreate(BaseModel):
    line_type: str = Field(..., max_length=20)
    description: str = Field(..., max_length=500)
    quantity: float = Field(0, ge=0, le=1_000_000_000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    total_cost: float = Field(0, ge=0, le=1_000_000_000_000)
    display_order: int = Field(0, ge=0, le=10000)

    @field_validator("line_type")
    @classmethod
    def validate_line_type(cls, v):
        allowed = {"labor", "material", "equipment"}
        if v not in allowed:
            raise ValueError(f"line_type must be one of {allowed}")
        return v


class TMTicketLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    company_id: int
    line_type: Optional[str] = None
    description: str
    quantity: float = 0
    unit: Optional[str] = None
    unit_cost: float = 0
    total_cost: float = 0
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# T&M TICKET
# =============================================================================

class TMTicketCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    ticket_number: Optional[str] = Field(None, max_length=100)
    date: date
    description: Optional[str] = None
    vendor_name: Optional[str] = Field(None, max_length=255)
    change_order_id: Optional[int] = None
    markup_pct: float = Field(0, ge=0, le=100)
    notes: Optional[str] = None
    lines: Optional[List[TMTicketLineCreate]] = Field(default=[], max_length=500)


class TMTicketUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_number: Optional[str] = Field(None, max_length=100)
    date: Optional[date] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    vendor_name: Optional[str] = Field(None, max_length=255)
    change_order_id: Optional[int] = None
    markup_pct: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = {"draft", "submitted", "approved", "billed", "void"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class TMTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    ticket_number: Optional[str] = None
    date: date
    description: Optional[str] = None
    status: Optional[str] = None
    change_order_id: Optional[int] = None
    vendor_name: Optional[str] = None
    labor_total: float = 0
    material_total: float = 0
    equipment_total: float = 0
    markup_pct: float = 0
    markup_amount: float = 0
    total_amount: float = 0
    submitted_by: Optional[int] = None
    approved_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TMTicketDetail(TMTicketResponse):
    lines: List[TMTicketLineResponse] = []
