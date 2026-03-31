"""API routes for BIM 3D Annotations"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_bim.models.annotation import BIMAnnotation3D
from addons.agcm_bim.schemas.bim import (
    BIMAnnotationCreate,
    BIMAnnotationUpdate,
    BIMAnnotationResponse,
)

router = APIRouter()


@router.get("/annotations", response_model=list[BIMAnnotationResponse])
async def list_annotations(
    project_id: Optional[int] = None,
    model_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List annotations, optionally filtered by project, model, or status."""
    company_id = get_effective_company_id(current_user, db)
    q = db.query(BIMAnnotation3D).filter(BIMAnnotation3D.company_id == company_id)

    if project_id is not None:
        q = q.filter(BIMAnnotation3D.project_id == project_id)
    if model_id is not None:
        q = q.filter(BIMAnnotation3D.model_id == model_id)
    if status is not None:
        q = q.filter(BIMAnnotation3D.status == status)

    q = q.order_by(BIMAnnotation3D.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.post("/annotations", response_model=BIMAnnotationResponse, status_code=201)
async def create_annotation(
    data: BIMAnnotationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new 3D annotation pinned to a model surface."""
    company_id = get_effective_company_id(current_user, db)
    annotation = BIMAnnotation3D(
        company_id=company_id,
        **data.model_dump(),
    )
    # Set audit fields
    if hasattr(annotation, "created_by"):
        annotation.created_by = current_user.id
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


@router.get("/annotations/{annotation_id}", response_model=BIMAnnotationResponse)
async def get_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single annotation by ID."""
    company_id = get_effective_company_id(current_user, db)
    annotation = (
        db.query(BIMAnnotation3D)
        .filter(
            BIMAnnotation3D.id == annotation_id,
            BIMAnnotation3D.company_id == company_id,
        )
        .first()
    )
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return annotation


@router.put("/annotations/{annotation_id}", response_model=BIMAnnotationResponse)
async def update_annotation(
    annotation_id: int,
    data: BIMAnnotationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing annotation."""
    company_id = get_effective_company_id(current_user, db)
    annotation = (
        db.query(BIMAnnotation3D)
        .filter(
            BIMAnnotation3D.id == annotation_id,
            BIMAnnotation3D.company_id == company_id,
        )
        .first()
    )
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(annotation, key, value)

    if hasattr(annotation, "updated_by"):
        annotation.updated_by = current_user.id

    db.commit()
    db.refresh(annotation)
    return annotation


@router.delete("/annotations/{annotation_id}", status_code=204)
async def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an annotation."""
    company_id = get_effective_company_id(current_user, db)
    annotation = (
        db.query(BIMAnnotation3D)
        .filter(
            BIMAnnotation3D.id == annotation_id,
            BIMAnnotation3D.company_id == company_id,
        )
        .first()
    )
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    db.delete(annotation)
    db.commit()


@router.post("/annotations/{annotation_id}/resolve", response_model=BIMAnnotationResponse)
async def resolve_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark an annotation as resolved."""
    company_id = get_effective_company_id(current_user, db)
    annotation = (
        db.query(BIMAnnotation3D)
        .filter(
            BIMAnnotation3D.id == annotation_id,
            BIMAnnotation3D.company_id == company_id,
        )
        .first()
    )
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    annotation.status = "resolved"
    if hasattr(annotation, "updated_by"):
        annotation.updated_by = current_user.id

    db.commit()
    db.refresh(annotation)
    return annotation
