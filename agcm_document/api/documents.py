"""API routes for Document Management"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_document.schemas.document import (
    FolderCreate, FolderUpdate, FolderResponse, FolderTreeResponse,
    DocumentCreate, DocumentUpdate, DocumentResponse,
)
from addons.agcm_document.services.document_service import DocumentService

router = APIRouter()

UPLOAD_DIR = "uploads/agcm/documents"


def _get_service(db: Session, current_user) -> DocumentService:
    company_id = get_effective_company_id(current_user, db)
    return DocumentService(db, company_id, current_user.id)


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------

@router.get("/folders", response_model=list[FolderTreeResponse])
async def get_folder_tree(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get hierarchical folder tree for a project."""
    svc = _get_service(db, current_user)
    return svc.get_folder_tree(project_id)


@router.post("/folders", response_model=FolderResponse, status_code=201)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_folder(data)


@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_folder(folder_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Folder not found")
    return result


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_folder(folder_id):
        raise HTTPException(status_code=404, detail="Folder not found")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@router.get("/documents")
async def list_documents(
    project_id: int,
    folder_id: Optional[int] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_documents(project_id, folder_id, document_type, status, search, page, page_size)
    result["items"] = [DocumentResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    doc = svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/documents/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    project_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    document_type: str = Form("other"),
    folder_id: int = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a document file and create the record."""
    svc = _get_service(db, current_user)

    # Save file
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    save_dir = os.path.join(UPLOAD_DIR, date_path)
    os.makedirs(save_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_url = f"/{file_path}"

    data = DocumentCreate(
        name=name,
        description=description,
        document_type=document_type,
        folder_id=folder_id,
        project_id=project_id,
    )
    return svc.create_document(data, file_name=file.filename, file_url=file_url)


@router.put("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_document(doc_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
