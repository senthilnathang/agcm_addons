"""Pydantic schemas for Payment Applications"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# PAYMENT APPLICATION LINE
# =============================================================================

class PaymentApplicationLineCreate(BaseModel):
    sov_line_id: Optional[int] = None
    description: str = Field(..., max_length=500)
    scheduled_value: float = Field(0, ge=0, le=1_000_000_000_000)
    previous_billed: float = Field(0, ge=0, le=1_000_000_000_000)
    current_billed: float = Field(0, ge=0, le=1_000_000_000_000)
    stored_materials: float = Field(0, ge=0, le=1_000_000_000_000)
    display_order: int = Field(0, ge=0, le=10000)


class PaymentApplicationLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    current_billed: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    stored_materials: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)


class PaymentApplicationLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    company_id: int
    sov_line_id: Optional[int] = None
    description: str
    scheduled_value: float = 0
    previous_billed: float = 0
    current_billed: float = 0
    stored_materials: float = 0
    total_completed: float = 0
    retainage: float = 0
    balance_to_finish: float = 0
    pct_complete: float = 0
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# PAYMENT APPLICATION
# =============================================================================

class PaymentApplicationCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    subcontract_id: int = Field(..., ge=1)
    application_number: int = Field(..., ge=1, le=9999)
    period_from: date
    period_to: date
    notes: Optional[str] = None


class PaymentApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    period_from: Optional[date] = None
    period_to: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    certified_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = {"draft", "submitted", "certified", "paid", "rejected"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class PaymentApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    application_number: int
    subcontract_id: int
    period_from: date
    period_to: date
    status: Optional[str] = None
    scheduled_value: float = 0
    previous_billed: float = 0
    current_billed: float = 0
    stored_materials: float = 0
    total_completed: float = 0
    retainage_held: float = 0
    retainage_released: float = 0
    net_payment_due: float = 0
    pct_complete: float = 0
    certified_by: Optional[str] = None
    certified_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentApplicationDetail(PaymentApplicationResponse):
    lines: List[PaymentApplicationLineResponse] = []
