"""Pydantic schemas for Vendor directory."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VendorCreate(BaseModel):
    name: str = Field(..., max_length=255)
    vendor_type: str = Field("vendor", description="vendor, client, subcontractor, supplier, architect, engineer, consultant, other")
    code: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)
    trade: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=100)
    insurance_expiry: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    vendor_type: Optional[str] = None
    code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    website: Optional[str] = None
    trade: Optional[str] = None
    license_number: Optional[str] = None
    insurance_expiry: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    vendor_type: Optional[str] = "vendor"
    code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    website: Optional[str] = None
    trade: Optional[str] = None
    license_number: Optional[str] = None
    insurance_expiry: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
