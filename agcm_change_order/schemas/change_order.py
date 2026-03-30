"""Pydantic schemas for Change Order module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Line Items ---

class ChangeOrderLineCreate(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: Optional[float] = 1.0
    unit: Optional[str] = None
    unit_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0


class ChangeOrderLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None


class ChangeOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    change_order_id: int
    description: str
    quantity: Optional[float] = 1.0
    unit: Optional[str] = None
    unit_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Change Order ---

class ChangeOrderCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    reason: Optional[str] = None
    cost_impact: Optional[float] = 0.0
    schedule_impact_days: Optional[int] = 0
    requested_date: Optional[date] = None
    project_id: int
    lines: Optional[List[ChangeOrderLineCreate]] = []


class ChangeOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    cost_impact: Optional[float] = None
    schedule_impact_days: Optional[int] = None
    requested_date: Optional[date] = None
    status: Optional[str] = None
    lines: Optional[List[ChangeOrderLineCreate]] = None


class ChangeOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    cost_impact: Optional[float] = 0.0
    schedule_impact_days: Optional[int] = 0
    requested_date: Optional[date] = None
    approved_date: Optional[date] = None
    project_id: int
    requested_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChangeOrderDetail(ChangeOrderResponse):
    """Extended response with line items."""
    lines: List[ChangeOrderLineResponse] = []
