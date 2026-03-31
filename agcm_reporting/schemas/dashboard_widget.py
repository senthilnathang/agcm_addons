"""Pydantic schemas for DashboardLayout and DashboardWidget"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- DashboardWidget ---

class DashboardWidgetBase(BaseModel):
    widget_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    config: Optional[str] = Field(None, max_length=10000)
    data_source: str = Field(..., max_length=100)
    position_x: int = Field(0, ge=0, le=100)
    position_y: int = Field(0, ge=0, le=100)
    width: int = Field(6, ge=1, le=24)
    height: int = Field(4, ge=1, le=24)
    display_order: int = Field(0, ge=0, le=9999)


class DashboardWidgetCreate(DashboardWidgetBase):
    pass


class DashboardWidgetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    widget_type: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    config: Optional[str] = Field(None, max_length=10000)
    data_source: Optional[str] = Field(None, max_length=100)
    position_x: Optional[int] = Field(None, ge=0, le=100)
    position_y: Optional[int] = Field(None, ge=0, le=100)
    width: Optional[int] = Field(None, ge=1, le=24)
    height: Optional[int] = Field(None, ge=1, le=24)
    display_order: Optional[int] = Field(None, ge=0, le=9999)


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
    layout_type: str = Field("executive", max_length=50)
    is_default: bool = False


class DashboardLayoutCreate(DashboardLayoutBase):
    widgets: Optional[List[DashboardWidgetCreate]] = []


class DashboardLayoutUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    layout_type: Optional[str] = Field(None, max_length=50)
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
