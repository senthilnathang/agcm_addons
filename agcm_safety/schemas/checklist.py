"""Pydantic schemas for Checklist Templates"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Template Items ---

class ChecklistTemplateItemCreate(BaseModel):
    description: str = Field(..., max_length=500)
    required: Optional[bool] = True
    display_order: Optional[int] = Field(0, ge=0, le=9999)


class ChecklistTemplateItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    description: str
    required: bool = True
    display_order: int = 0
    company_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Template ---

class ChecklistTemplateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = True
    items: Optional[List[ChecklistTemplateItemCreate]] = []


class ChecklistTemplateUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    items: Optional[List[ChecklistTemplateItemCreate]] = None


class ChecklistTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChecklistTemplateDetail(ChecklistTemplateResponse):
    """Extended response with items."""
    items: List[ChecklistTemplateItemResponse] = []
