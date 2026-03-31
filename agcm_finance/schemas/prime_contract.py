"""Pydantic schemas for Prime Contract"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PrimeContractCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    contract_number: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    owner_name: str = Field(..., max_length=255)
    status: str = Field("draft", max_length=20)
    original_value: float = Field(0, ge=0, le=1_000_000_000_000)
    approved_changes: float = Field(0, ge=-1_000_000_000_000, le=1_000_000_000_000)
    retainage_pct: float = Field(0, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    executed_date: Optional[date] = None
    contract_type: str = Field("lump_sum", max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"draft", "executed", "active", "complete", "closed"}
        if v and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v):
        allowed = {"lump_sum", "cost_plus", "gmp", "time_and_material", "unit_price"}
        if v and v not in allowed:
            raise ValueError(f"contract_type must be one of {allowed}")
        return v


class PrimeContractUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contract_number: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    owner_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=20)
    original_value: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    approved_changes: Optional[float] = Field(None, ge=-1_000_000_000_000, le=1_000_000_000_000)
    revised_value: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    billed_to_date: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    paid_to_date: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    retainage_held: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    retainage_pct: Optional[float] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    executed_date: Optional[date] = None
    contract_type: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = {"draft", "executed", "active", "complete", "closed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v):
        if v is None:
            return v
        allowed = {"lump_sum", "cost_plus", "gmp", "time_and_material", "unit_price"}
        if v not in allowed:
            raise ValueError(f"contract_type must be one of {allowed}")
        return v


class PrimeContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    contract_number: Optional[str] = None
    title: str
    description: Optional[str] = None
    owner_name: str
    status: Optional[str] = None
    original_value: float = 0
    approved_changes: float = 0
    revised_value: float = 0
    billed_to_date: float = 0
    paid_to_date: float = 0
    retainage_held: float = 0
    retainage_pct: float = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    executed_date: Optional[date] = None
    contract_type: str = "lump_sum"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
