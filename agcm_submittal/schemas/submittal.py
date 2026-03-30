"""Pydantic schemas for Submittal module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Approver
# ---------------------------------------------------------------------------

class ApproverCreate(BaseModel):
    user_id: int
    sequence: int = 1


class ApproverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    sequence: int
    status: str
    comments: Optional[str] = None
    signed_at: Optional[datetime] = None
    user_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Approve Action
# ---------------------------------------------------------------------------

class ApproveAction(BaseModel):
    action: str = Field(..., description="approve, approved_as_noted, reject, or revise_and_submit")
    comments: Optional[str] = None


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class SubmittalPackageCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    project_id: int


class SubmittalPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    project_id: int


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class SubmittalTypeCreate(BaseModel):
    name: str = Field(..., max_length=255)


class SubmittalTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

class SubmittalLabelCreate(BaseModel):
    name: str = Field(..., max_length=128)
    color: str = "#1890ff"


class SubmittalLabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str


# ---------------------------------------------------------------------------
# Submittal
# ---------------------------------------------------------------------------

class SubmittalCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    spec_section: Optional[str] = None
    project_id: int
    package_id: Optional[int] = None
    type_id: Optional[int] = None
    priority: str = "medium"
    due_date: Optional[date] = None
    submitted_date: Optional[date] = None
    received_date: Optional[date] = None
    label_ids: Optional[List[int]] = []
    approver_ids: Optional[List[ApproverCreate]] = []


class SubmittalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    spec_section: Optional[str] = None
    package_id: Optional[int] = None
    type_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    submitted_date: Optional[date] = None
    received_date: Optional[date] = None
    label_ids: Optional[List[int]] = None
    approver_ids: Optional[List[ApproverCreate]] = None


class SubmittalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    spec_section: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    revision: int = 1
    due_date: Optional[date] = None
    submitted_date: Optional[date] = None
    received_date: Optional[date] = None
    package_id: Optional[int] = None
    type_id: Optional[int] = None
    project_id: int
    submitted_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    package_name: Optional[str] = None
    type_name: Optional[str] = None


class SubmittalDetail(SubmittalResponse):
    """Extended response with approvers and labels"""
    approvers: List[ApproverResponse] = []
    label_ids: List[int] = []
    labels: List[SubmittalLabelResponse] = []
