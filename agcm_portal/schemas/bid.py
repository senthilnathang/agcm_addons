"""Pydantic schemas for BidPackage and BidSubmission"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- BidSubmission ---

class BidSubmissionBase(BaseModel):
    vendor_name: str = Field(..., max_length=255)
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    status: Optional[str] = "draft"
    total_amount: float = 0
    scope_description: Optional[str] = None
    exclusions: Optional[str] = None
    submitted_date: Optional[date] = None
    document_url: Optional[str] = None
    is_awarded: bool = False
    notes: Optional[str] = None


class BidSubmissionCreate(BidSubmissionBase):
    pass


class BidSubmissionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None
    scope_description: Optional[str] = None
    exclusions: Optional[str] = None
    submitted_date: Optional[date] = None
    document_url: Optional[str] = None
    is_awarded: Optional[bool] = None
    notes: Optional[str] = None


class BidSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bid_package_id: int
    company_id: int
    vendor_name: str
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    status: Optional[str] = None
    total_amount: float = 0
    scope_description: Optional[str] = None
    exclusions: Optional[str] = None
    submitted_date: Optional[date] = None
    document_url: Optional[str] = None
    is_awarded: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- BidPackage ---

class BidPackageBase(BaseModel):
    project_id: int
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trade: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = "open"
    notes: Optional[str] = None


class BidPackageCreate(BidPackageBase):
    pass


class BidPackageUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    trade: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BidPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    trade: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    submissions: List[BidSubmissionResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
