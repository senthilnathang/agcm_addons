"""Pydantic schemas for RFI module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Labels ---

class RFILabelCreate(BaseModel):
    name: str = Field(..., max_length=128)
    color: Optional[str] = "#1890ff"


class RFILabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: Optional[str] = None


# --- RFI ---

class RFICreate(BaseModel):
    subject: str = Field(..., max_length=500)
    question: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "draft"
    schedule_impact_days: Optional[int] = 0
    cost_impact: Optional[float] = 0.0
    due_date: Optional[date] = None
    project_id: int
    assignee_ids: Optional[List[int]] = []
    label_ids: Optional[List[int]] = []


class RFIUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subject: Optional[str] = None
    question: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    schedule_impact_days: Optional[int] = None
    cost_impact: Optional[float] = None
    due_date: Optional[date] = None
    assignee_ids: Optional[List[int]] = None
    label_ids: Optional[List[int]] = None


class RFIResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    subject: str
    question: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    schedule_impact_days: Optional[int] = 0
    cost_impact: Optional[float] = 0.0
    due_date: Optional[date] = None
    closed_date: Optional[date] = None
    project_id: int
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RFIDetail(RFIResponseSchema):
    assignee_ids: List[int] = []
    label_ids: List[int] = []
    labels: List[RFILabelResponse] = []
    response_count: int = 0
    responses: List[dict] = []


# --- RFI Responses (threaded) ---

class RFIResponseCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None
    is_official_response: Optional[bool] = False


class RFIResponseUpdate(BaseModel):
    content: Optional[str] = None
    is_official_response: Optional[bool] = None


class RFIResponseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfi_id: int
    parent_id: Optional[int] = None
    content: str
    is_official_response: bool = False
    responded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
