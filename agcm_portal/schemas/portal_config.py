"""Pydantic schemas for PortalConfig"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PortalConfigBase(BaseModel):
    project_id: int
    client_portal_enabled: bool = True
    sub_portal_enabled: bool = True
    show_budget: bool = False
    show_schedule: bool = True
    show_documents: bool = True
    show_photos: bool = True
    show_daily_logs: bool = False
    welcome_message: Optional[str] = Field(None, max_length=5000)


class PortalConfigCreate(PortalConfigBase):
    pass


class PortalConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    client_portal_enabled: Optional[bool] = None
    sub_portal_enabled: Optional[bool] = None
    show_budget: Optional[bool] = None
    show_schedule: Optional[bool] = None
    show_documents: Optional[bool] = None
    show_photos: Optional[bool] = None
    show_daily_logs: Optional[bool] = None
    welcome_message: Optional[str] = Field(None, max_length=5000)


class PortalConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    client_portal_enabled: bool = True
    sub_portal_enabled: bool = True
    show_budget: bool = False
    show_schedule: bool = True
    show_documents: bool = True
    show_photos: bool = True
    show_daily_logs: bool = False
    welcome_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
