"""Pydantic schemas for Document module"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Folders ---

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=255)
    parent_id: Optional[int] = None
    project_id: int


class FolderUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    parent_id: Optional[int] = None


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int] = None
    project_id: int
    created_at: Optional[datetime] = None


class FolderTreeResponse(FolderResponse):
    children: List["FolderTreeResponse"] = []
    document_count: int = 0


# --- Documents ---

class DocumentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = "other"
    folder_id: Optional[int] = None
    project_id: int


class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    folder_id: Optional[int] = None
    revision: Optional[int] = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    revision: int = 1
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    folder_id: Optional[int] = None
    project_id: int
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
