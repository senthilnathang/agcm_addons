"""Pydantic schemas for DashboardLayout and DashboardWidget"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- DashboardWidget ---

class DashboardWidgetBase(BaseModel):
    widget_type: str
    title: str = Field(..., max_length=255)
    config: Optional[str] = None  # JSON widget configuration
    data_source: str = Field(..., max_length=100)
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4
    display_order: int = 0


class DashboardWidgetCreate(DashboardWidgetBase):
    pass


class DashboardWidgetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    widget_type: Optional[str] = None
    title: Optional[str] = None
    config: Optional[str] = None
    data_source: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    display_order: Optional[int] = None


class DashboardWidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    layout_id: int
    company_id: int
    widget_type: Optional[str] = None
    title: str
    config: Optional[str] = None
    data_source: str
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- DashboardLayout ---

class DashboardLayoutBase(BaseModel):
    name: str = Field(..., max_length=255)
    layout_type: str = "executive"
    is_default: bool = False


class DashboardLayoutCreate(DashboardLayoutBase):
    widgets: Optional[List[DashboardWidgetCreate]] = []


class DashboardLayoutUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    layout_type: Optional[str] = None
    is_default: Optional[bool] = None


class DashboardLayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    layout_type: str = "executive"
    is_default: bool = False
    created_by: Optional[int] = None
    widgets: List[DashboardWidgetResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
