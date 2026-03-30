"""API routes for Project Images with multipart upload"""

import io
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_progress.schemas.progress import (
    ProjectImageUpdate, ProjectImageResponse,
)
from addons.agcm_progress.services.progress_service import ProgressService

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic"}

router = APIRouter()


def _get_service(db: Session, current_user) -> ProgressService:
    company_id = get_effective_company_id(current_user, db)
    return ProgressService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/project-images", response_model=None)
async def list_project_images(
    project_id: int = Query(..., description="Filter by project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List project images for a project."""
    svc = _get_service(db, current_user)
    items = svc.list_project_images(project_id)
    return {"items": items, "total": len(items)}


@router.post("/project-images/upload", response_model=None, status_code=201)
async def upload_project_image(
    project_id: int = Query(...),
    file: UploadFile = File(...),
    name: Optional[str] = Query(None, description="Image name/caption"),
    description: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    taken_on: Optional[str] = Query(None, description="Date taken (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a project image via multipart form."""
    company_id = get_effective_company_id(current_user, db)

    # Read file content with size check
    content = b""
    while chunk := await file.read(1024 * 1024):
        content += chunk
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    filename = file.filename or "image.jpg"
    filename = os.path.basename(filename).replace("..", "")
    mime_type = file.content_type or "image/jpeg"

    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP, HEIC")

    image_name = name or filename

    # Upload via storage
    document_id = None
    file_url = None
    storage_key = None

    try:
        from modules.storage.services.storage_registry import StorageRegistry
        registry = StorageRegistry(db)
        result = await registry.upload_file(
            file=io.BytesIO(content),
            filename=filename,
            company_id=company_id,
            content_type=mime_type,
            category="other",
        )
        storage_key = result.get("storage_key")
        file_url = f"/api/v1/storage/files/download/{storage_key}" if storage_key else None
    except Exception as e:
        logger.warning(f"Storage fallback: {e}")

    if not storage_key:
        try:
            from app.services.storage import StorageService
            storage_service = StorageService()
            result = await storage_service.upload_file(
                file=io.BytesIO(content),
                filename=filename,
                path="agcm/project-images",
                content_type=mime_type,
            )
            storage_key = result.get("storage_key") or result.get("key")
            file_url = result.get("url") or (f"/uploads/agcm/project-images/{storage_key}" if storage_key else None)
        except Exception as e:
            logger.warning(f"Storage fallback: {e}")

    # Last resort: local filesystem
    if not storage_key:
        import uuid
        from datetime import datetime
        upload_dir = os.path.join("uploads", "agcm", "project-images", datetime.now().strftime("%Y/%m/%d"))
        os.makedirs(upload_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(upload_dir, unique_name)
        with open(file_path, "wb") as f:
            f.write(content)
        storage_key = f"agcm/project-images/{datetime.now().strftime('%Y/%m/%d')}/{unique_name}"
        file_url = f"/uploads/{storage_key}"

    # Create Document record if available
    try:
        from modules.documents.models.document import Document
        import hashlib
        doc = Document(
            name=image_name,
            original_filename=filename,
            mime_type=mime_type,
            size=len(content),
            hash=hashlib.sha256(content).hexdigest(),
            file_extension=filename.rsplit(".", 1)[-1] if "." in filename else "",
            storage_key=storage_key,
            storage_backend="local",
            status="active",
            category="other",
            owner_id=current_user.id,
            company_id=company_id,
            current_version_number=1,
        )
        db.add(doc)
        db.flush()
        document_id = doc.id
    except Exception as e:
        logger.warning(f"Document record fallback: {e}")

    # Parse taken_on date
    taken_on_date = None
    if taken_on:
        try:
            from datetime import date as date_type
            taken_on_date = date_type.fromisoformat(taken_on)
        except ValueError:
            pass

    svc = _get_service(db, current_user)
    img = svc.create_project_image(
        project_id=project_id,
        name=image_name,
        file_name=filename,
        file_url=file_url,
        document_id=document_id,
        description=description,
        tags=tags,
        taken_on=taken_on_date,
    )
    return ProjectImageResponse.model_validate(img).model_dump()


@router.put("/project-images/{image_id}", response_model=None)
async def update_project_image(
    image_id: int,
    data: ProjectImageUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update project image metadata."""
    svc = _get_service(db, current_user)
    img = svc.update_project_image(image_id, data)
    if not img:
        raise HTTPException(status_code=404, detail="Project image not found")
    return ProjectImageResponse.model_validate(img).model_dump()


@router.delete("/project-images/{image_id}", status_code=204)
async def delete_project_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a project image."""
    svc = _get_service(db, current_user)
    if not svc.delete_project_image(image_id):
        raise HTTPException(status_code=404, detail="Project image not found")
