"""Pydantic schemas for Drawing module"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# DRAWING REVISION
# =============================================================================

class DrawingRevisionCreate(BaseModel):
    drawing_id: int = Field(..., ge=1)
    revision_number: str = Field(..., max_length=20)
    description: Optional[str] = None
    revision_date: Optional[date] = None
    document_id: Optional[int] = None
    file_url: Optional[str] = Field(None, max_length=500)
    issued_by: Optional[str] = Field(None, max_length=255)
    received_date: Optional[date] = None


class DrawingRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drawing_id: int
    company_id: int
    revision_number: str
    description: Optional[str] = None
    revision_date: Optional[date] = None
    document_id: Optional[int] = None
    file_url: Optional[str] = None
    issued_by: Optional[str] = None
    received_date: Optional[date] = None
    is_current: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# DRAWING
# =============================================================================

class DrawingCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    sheet_number: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    discipline: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    current_revision: str = Field("0", max_length=20)
    status: str = Field("current", max_length=20)
    received_date: Optional[date] = None
    folder_id: Optional[int] = None


class DrawingUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sheet_number: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    discipline: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    current_revision: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    received_date: Optional[date] = None
    folder_id: Optional[int] = None


class DrawingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    sheet_number: str
    title: str
    discipline: Optional[str] = None
    description: Optional[str] = None
    current_revision: str = "0"
    status: Optional[str] = None
    received_date: Optional[date] = None
    folder_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DrawingDetail(DrawingResponse):
    revisions: List[DrawingRevisionResponse] = []
