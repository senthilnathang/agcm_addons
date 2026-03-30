"""Pydantic schemas for Procurement module — PO, Subcontract, Vendor Bill."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# PURCHASE ORDER LINE
# =============================================================================

class PurchaseOrderLineCreate(BaseModel):
    cost_code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    item_type: str = Field("material", max_length=50)
    quantity: float = Field(0, ge=0, le=1_000_000_000)
    unit: str = Field("ea", max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    total_cost: float = Field(0, ge=0, le=1_000_000_000_000)
    display_order: int = Field(0, ge=0, le=10000)
    notes: Optional[str] = None

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        allowed = {"material", "labor", "equipment", "subcontractor", "fee", "allowance"}
        if v and v not in allowed:
            raise ValueError(f"item_type must be one of {allowed}")
        return v


class PurchaseOrderLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cost_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    item_type: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    total_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    display_order: Optional[int] = Field(None, ge=0, le=10000)
    notes: Optional[str] = None

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v is None:
            return v
        allowed = {"material", "labor", "equipment", "subcontractor", "fee", "allowance"}
        if v not in allowed:
            raise ValueError(f"item_type must be one of {allowed}")
        return v


class PurchaseOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_id: int
    company_id: int
    cost_code: Optional[str] = None
    description: str
    item_type: Optional[str] = None
    quantity: float = 0
    unit: str = "ea"
    unit_cost: float = 0
    total_cost: float = 0
    received_qty: float = 0
    display_order: int = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# PURCHASE ORDER
# =============================================================================

class PurchaseOrderCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    po_number: Optional[str] = Field(None, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    issue_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    shipping_method: Optional[str] = Field(None, max_length=100)
    shipping_address: Optional[str] = Field(None, max_length=2000)
    tax_amount: float = Field(0, ge=0, le=1_000_000_000)
    retainage_pct: float = Field(0, ge=0, le=100)
    estimate_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=5000)
    lines: Optional[List[PurchaseOrderLineCreate]] = Field(default=[], max_length=500)


class PurchaseOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    issue_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    shipping_method: Optional[str] = Field(None, max_length=100)
    shipping_address: Optional[str] = Field(None, max_length=2000)
    tax_amount: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    retainage_pct: Optional[float] = Field(None, ge=0, le=100)
    estimate_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=5000)


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    po_number: Optional[str] = None
    vendor_name: str
    vendor_contact: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    shipping_method: Optional[str] = None
    shipping_address: Optional[str] = None
    subtotal: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    retainage_pct: float = 0
    retainage_amount: float = 0
    estimate_id: Optional[int] = None
    approved_by: Optional[int] = None
    approved_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PurchaseOrderDetail(PurchaseOrderResponse):
    lines: List[PurchaseOrderLineResponse] = []
    received_pct: float = 0
    line_count: int = 0


# =============================================================================
# SUBCONTRACT SOV LINE
# =============================================================================

class SubcontractSOVLineCreate(BaseModel):
    cost_code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    scheduled_value: float = Field(0, ge=0, le=1_000_000_000_000)
    billed_previous: float = Field(0, ge=0, le=1_000_000_000_000)
    billed_current: float = Field(0, ge=0, le=1_000_000_000_000)
    stored_materials: float = Field(0, ge=0, le=1_000_000_000_000)
    display_order: int = Field(0, ge=0, le=10000)
    source_type: str = Field("original", max_length=50)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v):
        allowed = {"original", "change_order"}
        if v and v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v


class SubcontractSOVLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cost_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    scheduled_value: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    billed_previous: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    billed_current: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    stored_materials: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    display_order: Optional[int] = Field(None, ge=0, le=10000)
    source_type: Optional[str] = Field(None, max_length=50)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v):
        if v is None:
            return v
        allowed = {"original", "change_order"}
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v


class SubcontractSOVLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subcontract_id: int
    company_id: int
    cost_code: Optional[str] = None
    description: str
    scheduled_value: float = 0
    billed_previous: float = 0
    billed_current: float = 0
    stored_materials: float = 0
    total_completed: float = 0
    retainage: float = 0
    balance_to_finish: float = 0
    pct_complete: float = 0
    display_order: int = 0
    source_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# COMPLIANCE DOC
# =============================================================================

class ComplianceDocCreate(BaseModel):
    subcontract_id: int = Field(..., ge=1)
    doc_type: str = Field(..., max_length=50)
    status: str = Field("required", max_length=50)
    description: str = Field(..., min_length=1, max_length=255)
    expiration_date: Optional[date] = None
    document_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v):
        allowed = {
            "insurance_coi", "workers_comp", "bond", "license", "permit",
            "lien_waiver", "w9", "safety_cert", "other",
        }
        if v not in allowed:
            raise ValueError(f"doc_type must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"required", "submitted", "approved", "expired", "rejected"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ComplianceDocUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    expiration_date: Optional[date] = None
    document_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v):
        if v is None:
            return v
        allowed = {
            "insurance_coi", "workers_comp", "bond", "license", "permit",
            "lien_waiver", "w9", "safety_cert", "other",
        }
        if v not in allowed:
            raise ValueError(f"doc_type must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = {"required", "submitted", "approved", "expired", "rejected"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ComplianceDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subcontract_id: int
    company_id: int
    doc_type: Optional[str] = None
    status: Optional[str] = None
    description: str
    expiration_date: Optional[date] = None
    document_url: Optional[str] = None
    file_name: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# SUBCONTRACT
# =============================================================================

class SubcontractCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    contract_number: Optional[str] = Field(None, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    scope_of_work: Optional[str] = Field(None, max_length=10000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_amount: float = Field(0, ge=0, le=1_000_000_000_000)
    approved_cos: float = Field(0, ge=0, le=1_000_000_000_000)
    retainage_pct: float = Field(5.0, ge=0, le=100)
    estimate_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=5000)
    sov_lines: Optional[List[SubcontractSOVLineCreate]] = Field(default=[], max_length=500)


class SubcontractUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contract_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    scope_of_work: Optional[str] = Field(None, max_length=10000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_amount: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    approved_cos: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    retainage_pct: Optional[float] = Field(None, ge=0, le=100)
    estimate_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=5000)


class SubcontractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    contract_number: Optional[str] = None
    vendor_name: str
    vendor_contact: Optional[str] = None
    status: Optional[str] = None
    scope_of_work: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_amount: float = 0
    approved_cos: float = 0
    revised_amount: float = 0
    billed_to_date: float = 0
    paid_to_date: float = 0
    balance_remaining: float = 0
    retainage_pct: float = 5.0
    retainage_held: float = 0
    retainage_released: float = 0
    estimate_id: Optional[int] = None
    approved_by: Optional[int] = None
    approved_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SubcontractDetail(SubcontractResponse):
    sov_lines: List[SubcontractSOVLineResponse] = []
    compliance_docs: List[ComplianceDocResponse] = []
    sov_count: int = 0
    compliance_count: int = 0


# =============================================================================
# VENDOR BILL LINE
# =============================================================================

class VendorBillLineCreate(BaseModel):
    cost_code: Optional[str] = Field(None, max_length=50)
    po_line_id: Optional[int] = None
    line_type: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(0, ge=0, le=1_000_000_000)
    unit: str = Field("ea", max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    amount: float = Field(0, ge=0, le=1_000_000_000_000)
    display_order: int = Field(0, ge=0, le=10000)
    notes: Optional[str] = None

    @field_validator("line_type")
    @classmethod
    def validate_line_type(cls, v):
        if v is None:
            return v
        allowed = {
            "material", "labor", "equipment", "subcontractor",
            "allowance", "change_order", "other",
        }
        if v not in allowed:
            raise ValueError(f"line_type must be one of {allowed}")
        return v


class VendorBillLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cost_code: Optional[str] = Field(None, max_length=50)
    po_line_id: Optional[int] = None
    line_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    amount: Optional[float] = Field(None, ge=0, le=1_000_000_000_000)
    display_order: Optional[int] = Field(None, ge=0, le=10000)
    notes: Optional[str] = None

    @field_validator("line_type")
    @classmethod
    def validate_line_type(cls, v):
        if v is None:
            return v
        allowed = {
            "material", "labor", "equipment", "subcontractor",
            "allowance", "change_order", "other",
        }
        if v not in allowed:
            raise ValueError(f"line_type must be one of {allowed}")
        return v


class VendorBillLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bill_id: int
    company_id: int
    cost_code: Optional[str] = None
    po_line_id: Optional[int] = None
    line_type: Optional[str] = None
    description: str
    quantity: float = 0
    unit: str = "ea"
    unit_cost: float = 0
    amount: float = 0
    display_order: int = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# VENDOR BILL PAYMENT
# =============================================================================

class VendorBillPaymentCreate(BaseModel):
    payment_date: date
    amount: float = Field(..., gt=0, le=1_000_000_000_000)
    payment_method: str = Field(..., min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v):
        allowed = {"check", "wire", "ach", "cash", "credit_card"}
        if v not in allowed:
            raise ValueError(f"payment_method must be one of {allowed}")
        return v


class VendorBillPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bill_id: int
    company_id: int
    payment_date: date
    amount: float
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# VENDOR BILL
# =============================================================================

class VendorBillCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    bill_number: Optional[str] = Field(None, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    record_type: str = Field("bill", max_length=50)
    status: str = Field("draft", max_length=50)
    bill_reference: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_amount: float = Field(0, ge=0, le=1_000_000_000)
    payment_terms: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[int] = None
    subcontract_id: Optional[int] = None
    vendor_invoice_ref: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    lines: Optional[List[VendorBillLineCreate]] = []

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v):
        allowed = {"bill", "expense", "vendor_credit"}
        if v and v not in allowed:
            raise ValueError(f"record_type must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {
            "draft", "pending_approval", "approved", "partially_paid",
            "paid", "overdue", "cancelled",
        }
        if v and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class VendorBillUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bill_number: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor_contact: Optional[str] = Field(None, max_length=255)
    record_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    bill_reference: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_amount: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    payment_terms: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[int] = None
    subcontract_id: Optional[int] = None
    vendor_invoice_ref: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v):
        if v is None:
            return v
        allowed = {"bill", "expense", "vendor_credit"}
        if v not in allowed:
            raise ValueError(f"record_type must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = {
            "draft", "pending_approval", "approved", "partially_paid",
            "paid", "overdue", "cancelled",
        }
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class VendorBillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    bill_number: Optional[str] = None
    vendor_name: str
    vendor_contact: Optional[str] = None
    record_type: Optional[str] = None
    status: Optional[str] = None
    bill_reference: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    paid_amount: float = 0
    balance_due: float = 0
    payment_terms: Optional[str] = None
    purchase_order_id: Optional[int] = None
    subcontract_id: Optional[int] = None
    ocr_processed: bool = False
    ocr_confidence: Optional[float] = None
    original_file_url: Optional[str] = None
    vendor_invoice_ref: Optional[str] = None
    duplicate_flag: bool = False
    duplicate_of_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VendorBillDetail(VendorBillResponse):
    lines: List[VendorBillLineResponse] = []
    payments: List[VendorBillPaymentResponse] = []
    line_count: int = 0
    payment_count: int = 0


# =============================================================================
# MISC REQUEST SCHEMAS
# =============================================================================

class ReceiveDeliveryRequest(BaseModel):
    line_updates: List[dict] = Field(..., min_length=1)


class UpdateBillingRequest(BaseModel):
    sov_updates: List[dict] = Field(..., min_length=1)


class CreateFromEstimateRequest(BaseModel):
    estimate_id: int = Field(..., ge=1)
    vendor_name: str = Field(..., min_length=1, max_length=255)
