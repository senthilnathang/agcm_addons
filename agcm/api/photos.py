"""Photo API with multipart upload via core documents module"""

import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm.models.photo import Photo
from addons.agcm.models.daily_activity_log import DailyActivityLog
from addons.agcm.services.sequence_service import next_sequence

router = APIRouter()


@router.get("/photos", response_model=None)
async def list_photos(
    dailylog_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List photos for a daily log."""
    items = (
        db.query(Photo)
        .filter(Photo.dailylog_id == dailylog_id)
        .order_by(Photo.id.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": p.id,
                "sequence_name": p.sequence_name,
                "name": p.name,
                "file_name": p.file_name,
                "location": p.location,
                "album": p.album,
                "taken_on": str(p.taken_on) if p.taken_on else None,
                "document_id": p.document_id,
                "file_url": p.file_url,
                "dailylog_id": p.dailylog_id,
                "project_id": p.project_id,
                "created_at": str(p.created_at) if p.created_at else None,
            }
            for p in items
        ],
        "total": len(items),
    }


@router.post("/photos/upload", response_model=None, status_code=201)
async def upload_photo(
    dailylog_id: int = Query(...),
    file: UploadFile = File(...),
    name: Optional[str] = Query(None, description="Photo name/caption"),
    location: Optional[str] = Query(None),
    album: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload a photo via multipart form and store using core documents module.

    The file is uploaded to the documents module (local storage by default),
    and a Photo record is created linking to the document.
    """
    company_id = get_effective_company_id(current_user, db)

    # Get the daily log for project_id
    log = db.query(DailyActivityLog).filter(DailyActivityLog.id == dailylog_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    # Read file content
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    filename = file.filename or "photo.jpg"
    mime_type = file.content_type or "image/jpeg"
    photo_name = name or filename

    # Upload via documents module
    document_id = None
    file_url = None
    storage_key = None

    try:
        # Try StorageRegistry first (production path)
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
    except Exception:
        pass

    # Fallback: use default storage service
    if not storage_key:
        try:
            from app.services.storage import StorageService
            storage_service = StorageService()
            result = await storage_service.upload_file(
                file=io.BytesIO(content),
                filename=filename,
                path="agcm/photos",
                content_type=mime_type,
            )
            storage_key = result.get("storage_key") or result.get("key")
            file_url = result.get("url") or f"/uploads/agcm/photos/{storage_key}" if storage_key else None
        except Exception:
            pass

    # Last resort: save to local filesystem directly
    if not storage_key:
        import os
        import uuid
        from datetime import datetime
        upload_dir = os.path.join("uploads", "agcm", "photos", datetime.now().strftime("%Y/%m/%d"))
        os.makedirs(upload_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(upload_dir, unique_name)
        with open(file_path, "wb") as f:
            f.write(content)
        storage_key = f"agcm/photos/{datetime.now().strftime('%Y/%m/%d')}/{unique_name}"
        file_url = f"/uploads/{storage_key}"

    # Create Document record if documents module is available
    try:
        from modules.documents.models.document import Document
        import hashlib
        doc = Document(
            name=photo_name,
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
    except Exception:
        pass

    # Create Photo record
    photo = Photo(
        company_id=company_id,
        sequence_name=next_sequence(db, Photo, company_id),
        name=photo_name,
        file_name=filename,
        location=location,
        album=album,
        document_id=document_id,
        file_url=file_url,
        dailylog_id=dailylog_id,
        project_id=log.project_id,
        created_by=current_user.id,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {
        "id": photo.id,
        "sequence_name": photo.sequence_name,
        "name": photo.name,
        "file_name": photo.file_name,
        "file_url": photo.file_url,
        "document_id": photo.document_id,
        "dailylog_id": photo.dailylog_id,
    }


@router.delete("/photos/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a photo record."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(photo)
    db.commit()
