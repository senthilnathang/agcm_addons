"""Pydantic schemas for Finance module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# COST CODES
# =============================================================================

class CostCodeCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    category: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: int


class CostCodeUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[int] = None


class CostCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: int
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CostCodeTreeResponse(CostCodeResponse):
    """Cost code with nested children."""
    children: List["CostCodeTreeResponse"] = []


# =============================================================================
# BUDGETS
# =============================================================================

class BudgetCreate(BaseModel):
    project_id: int
    cost_code_id: Optional[int] = None
    description: str = Field(..., max_length=500)
    planned_amount: Optional[float] = 0
    actual_amount: Optional[float] = 0
    committed_amount: Optional[float] = 0


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cost_code_id: Optional[int] = None
    description: Optional[str] = None
    planned_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    committed_amount: Optional[float] = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    cost_code_id: Optional[int] = None
    description: str
    planned_amount: Optional[float] = 0
    actual_amount: Optional[float] = 0
    committed_amount: Optional[float] = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BudgetSummary(BaseModel):
    total_planned: float = 0
    total_actual: float = 0
    total_committed: float = 0
    variance: float = 0
    lines: List[BudgetResponse] = []


# =============================================================================
# EXPENSE LINES
# =============================================================================

class ExpenseLineCreate(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: Optional[float] = 1.0
    unit: Optional[str] = None
    unit_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0
    cost_code_id: Optional[int] = None
    category: Optional[str] = None


class ExpenseLineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    cost_code_id: Optional[int] = None
    category: Optional[str] = None


class ExpenseLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_id: int
    description: str
    quantity: Optional[float] = 1.0
    unit: Optional[str] = None
    unit_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0
    cost_code_id: Optional[int] = None
    category: Optional[str] = None
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# EXPENSES
# =============================================================================

class ExpenseCreate(BaseModel):
    description: str = Field(..., max_length=500)
    vendor: Optional[str] = None
    project_id: int
    lines: Optional[List[ExpenseLineCreate]] = []


class ExpenseUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = None
    vendor: Optional[str] = None
    status: Optional[str] = None
    lines: Optional[List[ExpenseLineCreate]] = None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    description: str
    vendor: Optional[str] = None
    status: Optional[str] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExpenseDetail(ExpenseResponse):
    """Extended response with line items."""
    lines: List[ExpenseLineResponse] = []


# =============================================================================
# INVOICES
# =============================================================================

class InvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    client_name: str = Field(..., max_length=255)
    amount: Optional[float] = 0
    tax_amount: Optional[float] = 0
    total_amount: Optional[float] = 0
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    project_id: int


class InvoiceUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    invoice_number: Optional[str] = None
    client_name: str
    status: Optional[str] = None
    amount: Optional[float] = 0
    tax_amount: Optional[float] = 0
    total_amount: Optional[float] = 0
    paid_amount: Optional[float] = 0
    balance_due: Optional[float] = 0
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# BILLS
# =============================================================================

class BillCreate(BaseModel):
    bill_number: Optional[str] = None
    vendor_name: str = Field(..., max_length=255)
    amount: Optional[float] = 0
    tax_amount: Optional[float] = 0
    total_amount: Optional[float] = 0
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    project_id: int


class BillUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bill_number: Optional[str] = None
    vendor_name: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None


class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    bill_number: Optional[str] = None
    vendor_name: str
    status: Optional[str] = None
    amount: Optional[float] = 0
    tax_amount: Optional[float] = 0
    total_amount: Optional[float] = 0
    paid_amount: Optional[float] = 0
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    project_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# RECORD PAYMENT (shared for invoices and bills)
# =============================================================================

class RecordPayment(BaseModel):
    amount: float = Field(..., gt=0)
