"""Pydantic schemas for AGCM Estimate module — all CRUD schemas in one file."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Allowed enum values for validation
ITEM_TYPES = ("material", "labor", "equipment", "subcontractor", "fee", "other")
LINE_ITEM_TYPES = ("material", "labor", "equipment", "subcontractor", "fee", "allowance", "assembly")
ESTIMATE_TYPES = ("preliminary", "schematic", "detailed", "change_order")
ESTIMATE_STATUSES = ("draft", "in_review", "approved", "rejected", "superseded")
MARKUP_TYPES = ("percentage", "lump_sum")
MEASUREMENT_TYPES = ("linear", "area", "count")


# =============================================================================
# COST CATALOG
# =============================================================================

class CostCatalogCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_default: bool = False


class CostCatalogUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_default: Optional[bool] = None


class CostCatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# COST ITEM
# =============================================================================

class CostItemCreate(BaseModel):
    catalog_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: str = Field("material", description="One of: material, labor, equipment, subcontractor, fee, other")
    unit: str = Field("ea", max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    unit_price: float = Field(0, ge=0, le=1_000_000_000)
    taxable: bool = True
    cost_code: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        if v not in ITEM_TYPES:
            raise ValueError(f"item_type must be one of {ITEM_TYPES}")
        return v


class CostItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unit_price: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    taxable: Optional[bool] = None
    cost_code: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v is not None and v not in ITEM_TYPES:
            raise ValueError(f"item_type must be one of {ITEM_TYPES}")
        return v


class CostItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    catalog_id: int
    name: str
    description: Optional[str] = None
    item_type: str
    unit: str = "ea"
    unit_cost: float = 0
    unit_price: float = 0
    taxable: bool = True
    cost_code: Optional[str] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ASSEMBLY
# =============================================================================

class AssemblyItemCreate(BaseModel):
    cost_item_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: str = Field("material", description="One of: material, labor, equipment, subcontractor, fee, other")
    quantity: float = Field(1, ge=0, le=1_000_000)
    unit: str = Field("ea", max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    waste_factor: float = Field(0, ge=0, le=100)

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        if v not in ITEM_TYPES:
            raise ValueError(f"item_type must be one of {ITEM_TYPES}")
        return v


class AssemblyItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cost_item_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0, le=1_000_000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    waste_factor: Optional[float] = Field(None, ge=0, le=100)

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v is not None and v not in ITEM_TYPES:
            raise ValueError(f"item_type must be one of {ITEM_TYPES}")
        return v


class AssemblyItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assembly_id: int
    cost_item_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    item_type: str
    quantity: float = 1
    unit: str = "ea"
    unit_cost: float = 0
    waste_factor: float = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssemblyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    items: Optional[List[AssemblyItemCreate]] = Field(default=[], max_length=500)


class AssemblyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class AssemblyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssemblyDetail(AssemblyResponse):
    items: List[AssemblyItemResponse] = []


# =============================================================================
# ESTIMATE
# =============================================================================

class EstimateCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    estimate_type: str = Field("detailed", description="One of: preliminary, schematic, detailed, change_order")
    tax_rate: float = Field(0, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=5000)

    @field_validator("estimate_type")
    @classmethod
    def validate_estimate_type(cls, v: str) -> str:
        if v not in ESTIMATE_TYPES:
            raise ValueError(f"estimate_type must be one of {ESTIMATE_TYPES}")
        return v


class EstimateUpdate(BaseModel):
    """Update an estimate. Note: status changes must go through dedicated
    endpoints (approve, create-version) to enforce workflow rules."""
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    estimate_type: Optional[str] = None
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=5000)

    @field_validator("estimate_type")
    @classmethod
    def validate_estimate_type(cls, v):
        if v is not None and v not in ESTIMATE_TYPES:
            raise ValueError(f"estimate_type must be one of {ESTIMATE_TYPES}")
        return v


class EstimateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    sequence_name: Optional[str] = None
    project_id: int
    name: str
    description: Optional[str] = None
    version: int = 1
    status: str = "draft"
    estimate_type: str = "detailed"
    subtotal: float = 0
    markup_total: float = 0
    tax_total: float = 0
    grand_total: float = 0
    tax_rate: float = 0
    notes: Optional[str] = None
    approved_by: Optional[int] = None
    approved_date: Optional[date] = None
    parent_estimate_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ESTIMATE GROUP
# =============================================================================

class EstimateGroupCreate(BaseModel):
    estimate_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    display_order: int = Field(0, ge=0, le=10000)


class EstimateGroupUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    display_order: Optional[int] = Field(None, ge=0, le=10000)


class EstimateGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estimate_id: int
    name: str
    description: Optional[str] = None
    display_order: int = 0
    subtotal: float = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ESTIMATE LINE ITEM
# =============================================================================

class EstimateLineItemCreate(BaseModel):
    group_id: int
    estimate_id: int
    cost_item_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: str = Field("material", description="One of: material, labor, equipment, subcontractor, fee, allowance, assembly")
    quantity: float = Field(0, ge=0, le=1_000_000)
    unit: str = Field("ea", max_length=50)
    unit_cost: float = Field(0, ge=0, le=1_000_000_000)
    unit_price: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    markup_pct: float = Field(0, ge=-100, le=1000)
    taxable: bool = True
    cost_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=5000)
    display_order: int = Field(0, ge=0, le=10000)

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        if v not in LINE_ITEM_TYPES:
            raise ValueError(f"item_type must be one of {LINE_ITEM_TYPES}")
        return v


class EstimateLineItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    item_type: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0, le=1_000_000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_cost: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unit_price: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    markup_pct: Optional[float] = Field(None, ge=-100, le=1000)
    taxable: Optional[bool] = None
    cost_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=5000)
    display_order: Optional[int] = Field(None, ge=0, le=10000)

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v is not None and v not in LINE_ITEM_TYPES:
            raise ValueError(f"item_type must be one of {LINE_ITEM_TYPES}")
        return v


class EstimateLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    estimate_id: int
    cost_item_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    item_type: str
    quantity: float = 0
    unit: str = "ea"
    unit_cost: float = 0
    unit_price: float = 0
    total_cost: float = 0
    total_price: float = 0
    markup_pct: float = 0
    taxable: bool = True
    cost_code: Optional[str] = None
    notes: Optional[str] = None
    display_order: int = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ESTIMATE MARKUP
# =============================================================================

class EstimateMarkupCreate(BaseModel):
    estimate_id: int
    name: str = Field(..., min_length=1, max_length=255)
    markup_type: str = Field("percentage", description="One of: percentage, lump_sum")
    value: float = Field(0, ge=-1_000_000_000, le=1_000_000_000)
    apply_before_tax: bool = True
    is_compounding: bool = False
    display_order: int = Field(0, ge=0, le=10000)

    @field_validator("markup_type")
    @classmethod
    def validate_markup_type(cls, v: str) -> str:
        if v not in MARKUP_TYPES:
            raise ValueError(f"markup_type must be one of {MARKUP_TYPES}")
        return v


class EstimateMarkupUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    markup_type: Optional[str] = None
    value: Optional[float] = Field(None, ge=-1_000_000_000, le=1_000_000_000)
    apply_before_tax: Optional[bool] = None
    is_compounding: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0, le=10000)

    @field_validator("markup_type")
    @classmethod
    def validate_markup_type(cls, v):
        if v is not None and v not in MARKUP_TYPES:
            raise ValueError(f"markup_type must be one of {MARKUP_TYPES}")
        return v


class EstimateMarkupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estimate_id: int
    name: str
    markup_type: str
    value: float = 0
    apply_before_tax: bool = True
    is_compounding: bool = False
    display_order: int = 0
    calculated_amount: float = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ESTIMATE SUMMARY
# =============================================================================

class EstimateSummary(BaseModel):
    subtotal: float = 0
    markup_total: float = 0
    tax_total: float = 0
    grand_total: float = 0
    line_item_count: int = 0
    group_count: int = 0


# =============================================================================
# ESTIMATE DETAIL (full nested response)
# =============================================================================

class EstimateGroupDetail(EstimateGroupResponse):
    line_items: List[EstimateLineItemResponse] = []


class EstimateDetail(EstimateResponse):
    groups: List[EstimateGroupDetail] = []
    markups: List[EstimateMarkupResponse] = []
    summary: Optional[EstimateSummary] = None


# =============================================================================
# PROPOSAL
# =============================================================================

class ProposalCreate(BaseModel):
    estimate_id: int
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    client_name: str = Field(..., min_length=1, max_length=255)
    client_email: Optional[str] = Field(None, max_length=255)
    client_phone: Optional[str] = Field(None, max_length=50)
    scope_of_work: Optional[str] = Field(None, max_length=50000)
    terms_and_conditions: Optional[str] = Field(None, max_length=50000)
    exclusions: Optional[str] = Field(None, max_length=50000)
    payment_schedule: Optional[str] = Field(None, max_length=50000)
    valid_until: Optional[date] = None
    show_line_items: bool = True
    show_unit_prices: bool = False
    show_markup: bool = False
    show_groups: bool = True
    notes: Optional[str] = Field(None, max_length=5000)


class ProposalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_email: Optional[str] = Field(None, max_length=255)
    client_phone: Optional[str] = Field(None, max_length=50)
    scope_of_work: Optional[str] = Field(None, max_length=50000)
    terms_and_conditions: Optional[str] = Field(None, max_length=50000)
    exclusions: Optional[str] = Field(None, max_length=50000)
    payment_schedule: Optional[str] = Field(None, max_length=50000)
    valid_until: Optional[date] = None
    show_line_items: Optional[bool] = None
    show_unit_prices: Optional[bool] = None
    show_markup: Optional[bool] = None
    show_groups: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=5000)


class ProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    sequence_name: Optional[str] = None
    estimate_id: int
    project_id: int
    name: str
    description: Optional[str] = None
    status: str = "draft"
    client_name: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    scope_of_work: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    exclusions: Optional[str] = None
    payment_schedule: Optional[str] = None
    valid_until: Optional[date] = None
    sent_date: Optional[date] = None
    viewed_date: Optional[datetime] = None
    approved_date: Optional[date] = None
    show_line_items: bool = True
    show_unit_prices: bool = False
    show_markup: bool = False
    show_groups: bool = True
    notes: Optional[str] = None
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# TAKEOFF SHEET
# =============================================================================

class TakeoffSheetCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    file_name: Optional[str] = Field(None, max_length=500)
    file_url: Optional[str] = Field(None, max_length=1000)
    document_id: Optional[int] = None
    page_number: int = Field(1, ge=1, le=10000)
    scale_factor: float = Field(1.0, gt=0, le=10000)
    scale_unit: str = Field("ft", max_length=20)


class TakeoffSheetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    file_name: Optional[str] = Field(None, max_length=500)
    file_url: Optional[str] = Field(None, max_length=1000)
    document_id: Optional[int] = None
    page_number: Optional[int] = Field(None, ge=1, le=10000)
    scale_factor: Optional[float] = Field(None, gt=0, le=10000)
    scale_unit: Optional[str] = Field(None, max_length=20)
    revision: Optional[int] = Field(None, ge=1, le=10000)


class TakeoffSheetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    sequence_name: Optional[str] = None
    project_id: int
    name: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    document_id: Optional[int] = None
    page_number: int = 1
    scale_factor: float = 1.0
    scale_unit: str = "ft"
    revision: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# TAKEOFF MEASUREMENT
# =============================================================================

class TakeoffMeasurementCreate(BaseModel):
    sheet_id: int
    estimate_line_item_id: Optional[int] = None
    measurement_type: str = Field("linear", description="One of: linear, area, count")
    label: Optional[str] = Field(None, max_length=255)
    value: float = Field(0, ge=0, le=1_000_000_000)
    unit: str = Field("ft", max_length=20)
    points_json: Optional[str] = Field(None, max_length=100000)
    color: str = Field("#1890ff", max_length=20, pattern=r"^#[0-9a-fA-F]{3,8}$")
    layer: Optional[str] = Field(None, max_length=100)

    @field_validator("measurement_type")
    @classmethod
    def validate_measurement_type(cls, v: str) -> str:
        if v not in MEASUREMENT_TYPES:
            raise ValueError(f"measurement_type must be one of {MEASUREMENT_TYPES}")
        return v


class TakeoffMeasurementUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    estimate_line_item_id: Optional[int] = None
    measurement_type: Optional[str] = None
    label: Optional[str] = Field(None, max_length=255)
    value: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unit: Optional[str] = Field(None, max_length=20)
    points_json: Optional[str] = Field(None, max_length=100000)
    color: Optional[str] = Field(None, max_length=20, pattern=r"^#[0-9a-fA-F]{3,8}$")
    layer: Optional[str] = Field(None, max_length=100)

    @field_validator("measurement_type")
    @classmethod
    def validate_measurement_type(cls, v):
        if v is not None and v not in MEASUREMENT_TYPES:
            raise ValueError(f"measurement_type must be one of {MEASUREMENT_TYPES}")
        return v


class TakeoffMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sheet_id: int
    estimate_line_item_id: Optional[int] = None
    measurement_type: str
    label: Optional[str] = None
    value: float = 0
    unit: str = "ft"
    points_json: Optional[str] = None
    color: str = "#1890ff"
    layer: Optional[str] = None
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ADD ASSEMBLY TO ESTIMATE
# =============================================================================

class AddAssemblyRequest(BaseModel):
    group_id: int
    assembly_id: int
    quantity_multiplier: float = Field(1.0, gt=0, le=1_000_000)
