"""Pydantic schemas for Selection and SelectionOption"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- SelectionOption ---

class SelectionOptionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: float = 0
    unit: Optional[str] = None
    image_url: Optional[str] = None
    spec_url: Optional[str] = None
    is_recommended: bool = False
    is_selected: bool = False
    display_order: int = 0


class SelectionOptionCreate(SelectionOptionBase):
    pass


class SelectionOptionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    image_url: Optional[str] = None
    spec_url: Optional[str] = None
    is_recommended: Optional[bool] = None
    is_selected: Optional[bool] = None
    display_order: Optional[int] = None


class SelectionOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    selection_id: int
    company_id: int
    name: str
    description: Optional[str] = None
    price: float = 0
    unit: Optional[str] = None
    image_url: Optional[str] = None
    spec_url: Optional[str] = None
    is_recommended: bool = False
    is_selected: bool = False
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Selection ---

class SelectionBase(BaseModel):
    project_id: int
    name: str = Field(..., max_length=255)
    category: str = Field(..., max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "pending"
    due_date: Optional[date] = None
    decided_date: Optional[date] = None
    budget_amount: float = 0
    selected_amount: float = 0
    budget_impact: float = 0
    decided_by: Optional[str] = None
    notes: Optional[str] = None


class SelectionCreate(SelectionBase):
    options: Optional[List[SelectionOptionCreate]] = []


class SelectionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    decided_date: Optional[date] = None
    budget_amount: Optional[float] = None
    selected_amount: Optional[float] = None
    budget_impact: Optional[float] = None
    decided_by: Optional[str] = None
    notes: Optional[str] = None


class SelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    name: str
    category: str
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    decided_date: Optional[date] = None
    budget_amount: float = 0
    selected_amount: float = 0
    budget_impact: float = 0
    decided_by: Optional[str] = None
    notes: Optional[str] = None
    options: List[SelectionOptionResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
