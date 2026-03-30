"""Pydantic schemas for AGCM Estimate module — all CRUD schemas in one file."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# COST CATALOG
# =============================================================================

class CostCatalogCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_default: bool = False


class CostCatalogUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    item_type: str = "material"
    unit: str = "ea"
    unit_cost: float = 0
    unit_price: float = 0
    taxable: bool = True
    cost_code: Optional[str] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True


class CostItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    taxable: Optional[bool] = None
    cost_code: Optional[str] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    item_type: str = "material"
    quantity: float = 1
    unit: str = "ea"
    unit_cost: float = 0
    waste_factor: float = 0


class AssemblyItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cost_item_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    waste_factor: Optional[float] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    items: Optional[List[AssemblyItemCreate]] = []


class AssemblyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    estimate_type: str = "detailed"
    tax_rate: float = 0
    notes: Optional[str] = None


class EstimateUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    estimate_type: Optional[str] = None
    status: Optional[str] = None
    tax_rate: Optional[float] = None
    notes: Optional[str] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    display_order: int = 0


class EstimateGroupUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    item_type: str = "material"
    quantity: float = 0
    unit: str = "ea"
    unit_cost: float = 0
    unit_price: Optional[float] = None
    markup_pct: float = 0
    taxable: bool = True
    cost_code: Optional[str] = None
    notes: Optional[str] = None
    display_order: int = 0


class EstimateLineItemUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    markup_pct: Optional[float] = None
    taxable: Optional[bool] = None
    cost_code: Optional[str] = None
    notes: Optional[str] = None
    display_order: Optional[int] = None


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
    name: str = Field(..., max_length=255)
    markup_type: str = "percentage"
    value: float = 0
    apply_before_tax: bool = True
    is_compounding: bool = False
    display_order: int = 0


class EstimateMarkupUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    markup_type: Optional[str] = None
    value: Optional[float] = None
    apply_before_tax: Optional[bool] = None
    is_compounding: Optional[bool] = None
    display_order: Optional[int] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    client_name: str = Field(..., max_length=255)
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    scope_of_work: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    exclusions: Optional[str] = None
    payment_schedule: Optional[str] = None
    valid_until: Optional[date] = None
    show_line_items: bool = True
    show_unit_prices: bool = False
    show_markup: bool = False
    show_groups: bool = True
    notes: Optional[str] = None


class ProposalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    scope_of_work: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    exclusions: Optional[str] = None
    payment_schedule: Optional[str] = None
    valid_until: Optional[date] = None
    show_line_items: Optional[bool] = None
    show_unit_prices: Optional[bool] = None
    show_markup: Optional[bool] = None
    show_groups: Optional[bool] = None
    notes: Optional[str] = None


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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    document_id: Optional[int] = None
    page_number: int = 1
    scale_factor: float = 1.0
    scale_unit: str = "ft"


class TakeoffSheetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    document_id: Optional[int] = None
    page_number: Optional[int] = None
    scale_factor: Optional[float] = None
    scale_unit: Optional[str] = None
    revision: Optional[int] = None


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
    measurement_type: str = "linear"
    label: Optional[str] = None
    value: float = 0
    unit: str = "ft"
    points_json: Optional[str] = None
    color: str = "#1890ff"
    layer: Optional[str] = None


class TakeoffMeasurementUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    estimate_line_item_id: Optional[int] = None
    measurement_type: Optional[str] = None
    label: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    points_json: Optional[str] = None
    color: Optional[str] = None
    layer: Optional[str] = None


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
    quantity_multiplier: float = 1.0
