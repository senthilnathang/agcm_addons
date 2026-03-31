"""API routes for Drawing Management"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_document.models.drawing import Drawing, DrawingRevision
from addons.agcm_document.schemas.drawing import (
    DrawingCreate, DrawingUpdate, DrawingResponse, DrawingDetail,
    DrawingRevisionCreate, DrawingRevisionResponse,
)

router = APIRouter()

SEQUENCE_PREFIX = "DWG"
SEQUENCE_PADDING = 5


def _next_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(Drawing.sequence_name)
        .filter(Drawing.company_id == company_id, Drawing.sequence_name.isnot(None))
        .order_by(Drawing.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


@router.get("/drawings")
async def list_drawings(
    project_id: int = Query(..., ge=1),
    discipline: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    query = db.query(Drawing).filter(
        Drawing.company_id == company_id,
        Drawing.project_id == project_id,
    )
    if discipline:
        query = query.filter(Drawing.discipline == discipline)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Drawing.title.ilike(term)) | (Drawing.sheet_number.ilike(term))
        )
    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(Drawing.sheet_number).offset(skip).limit(page_size).all()
    return {
        "items": [DrawingResponse.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/drawings/{drawing_id}")
async def get_drawing(
    drawing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    drawing = (
        db.query(Drawing)
        .filter(Drawing.id == drawing_id, Drawing.company_id == company_id)
        .first()
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return DrawingDetail.model_validate(drawing).model_dump()


@router.post("/drawings", status_code=201)
async def create_drawing(
    data: DrawingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    drawing = Drawing(
        company_id=company_id,
        project_id=data.project_id,
        sequence_name=_next_sequence(db, company_id),
        sheet_number=data.sheet_number,
        title=data.title,
        discipline=data.discipline,
        description=data.description,
        current_revision=data.current_revision,
        status=data.status,
        received_date=data.received_date,
        folder_id=data.folder_id,
        created_by=current_user.id,
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return DrawingResponse.model_validate(drawing).model_dump()


@router.put("/drawings/{drawing_id}")
async def update_drawing(
    drawing_id: int,
    data: DrawingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    drawing = (
        db.query(Drawing)
        .filter(Drawing.id == drawing_id, Drawing.company_id == company_id)
        .first()
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(drawing, key, value)
    drawing.updated_by = current_user.id
    db.commit()
    db.refresh(drawing)
    return DrawingResponse.model_validate(drawing).model_dump()


@router.delete("/drawings/{drawing_id}", status_code=204)
async def delete_drawing(
    drawing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    drawing = (
        db.query(Drawing)
        .filter(Drawing.id == drawing_id, Drawing.company_id == company_id)
        .first()
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    db.delete(drawing)
    db.commit()


# ---------------------------------------------------------------------------
# Drawing Revisions
# ---------------------------------------------------------------------------

@router.post("/drawing-revisions", status_code=201)
async def create_drawing_revision(
    data: DrawingRevisionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    drawing = (
        db.query(Drawing)
        .filter(Drawing.id == data.drawing_id, Drawing.company_id == company_id)
        .first()
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    # Supersede previous current revisions
    db.query(DrawingRevision).filter(
        DrawingRevision.drawing_id == data.drawing_id,
        DrawingRevision.is_current == True,  # noqa: E712
    ).update({"is_current": False})

    revision = DrawingRevision(
        drawing_id=data.drawing_id,
        company_id=company_id,
        revision_number=data.revision_number,
        description=data.description,
        revision_date=data.revision_date,
        document_id=data.document_id,
        file_url=data.file_url,
        issued_by=data.issued_by,
        received_date=data.received_date,
        is_current=True,
    )
    db.add(revision)

    # Update drawing's current revision
    drawing.current_revision = data.revision_number
    drawing.updated_by = current_user.id

    db.commit()
    db.refresh(revision)
    return DrawingRevisionResponse.model_validate(revision).model_dump()


@router.get("/drawing-revisions")
async def list_drawing_revisions(
    drawing_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    revisions = (
        db.query(DrawingRevision)
        .filter(
            DrawingRevision.drawing_id == drawing_id,
            DrawingRevision.company_id == company_id,
        )
        .order_by(DrawingRevision.id.desc())
        .all()
    )
    return [DrawingRevisionResponse.model_validate(r).model_dump() for r in revisions]
