"""API routes for Submittal module"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import insert, delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id
from addons.agcm.models.entity_attachment import agcm_entity_attachments

from addons.agcm_submittal.schemas.submittal import (
    ApproveAction,
    SubmittalCreate,
    SubmittalUpdate,
    SubmittalResponse,
    SubmittalDetail,
    SubmittalPackageCreate,
    SubmittalPackageResponse,
    SubmittalTypeCreate,
    SubmittalTypeResponse,
    SubmittalLabelCreate,
    SubmittalLabelResponse,
)
from addons.agcm_submittal.services.submittal_service import SubmittalService

router = APIRouter()


def _get_service(db: Session, current_user) -> SubmittalService:
    company_id = get_effective_company_id(current_user, db)
    return SubmittalService(db=db, company_id=company_id, user_id=current_user.id)


# ---------------------------------------------------------------------------
# Submittals
# ---------------------------------------------------------------------------

@router.get("/submittals", response_model=None)
async def list_submittals(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List submittals with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_submittals(
        project_id=project_id,
        status=status,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/submittals/{submittal_id}", response_model=None)
async def get_submittal(
    submittal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get submittal details with approvers and labels."""
    svc = _get_service(db, current_user)
    detail = svc.get_submittal_detail(submittal_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Submittal not found")
    return detail


@router.post("/submittals", response_model=None, status_code=201)
async def create_submittal(
    data: SubmittalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new submittal."""
    svc = _get_service(db, current_user)
    submittal = svc.create_submittal(data)
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.submittal_created(db, submittal)
    except Exception:
        pass
    return SubmittalResponse.model_validate(submittal).model_dump()


@router.put("/submittals/{submittal_id}", response_model=None)
async def update_submittal(
    submittal_id: int,
    data: SubmittalUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a submittal."""
    svc = _get_service(db, current_user)
    submittal = svc.update_submittal(submittal_id, data)
    if not submittal:
        raise HTTPException(status_code=404, detail="Submittal not found")
    return SubmittalResponse.model_validate(submittal).model_dump()


@router.delete("/submittals/{submittal_id}", status_code=204)
async def delete_submittal(
    submittal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a submittal."""
    svc = _get_service(db, current_user)
    if not svc.delete_submittal(submittal_id):
        raise HTTPException(status_code=404, detail="Submittal not found")


@router.post("/submittals/{submittal_id}/approve", response_model=None)
async def approve_submittal(
    submittal_id: int,
    body: ApproveAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve, reject, or request revision on a submittal."""
    svc = _get_service(db, current_user)
    old_submittal = svc.get_submittal(submittal_id)
    old_status = str(old_submittal.status) if old_submittal and old_submittal.status else None
    result = svc.approve_submittal(submittal_id, body.action, body.comments)
    if not result:
        raise HTTPException(status_code=404, detail="Submittal not found")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        updated = svc.get_submittal(submittal_id)
        if updated and old_status:
            new_status = str(updated.status) if updated.status else None
            if new_status and old_status != new_status:
                await agcm_realtime.submittal_status_changed(db, updated, old_status, new_status)
    except Exception:
        pass
    return result


@router.post("/submittals/{submittal_id}/resubmit", response_model=None)
async def resubmit_submittal(
    submittal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Resubmit a rejected submittal (increments revision)."""
    svc = _get_service(db, current_user)
    result = svc.resubmit_submittal(submittal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Submittal not found")
    return result


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

@router.get("/submittal-packages", response_model=list[SubmittalPackageResponse])
async def list_packages(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
):
    """List submittal packages."""
    svc = _get_service(db, current_user)
    return svc.list_packages(project_id=project_id)


@router.post("/submittal-packages", response_model=SubmittalPackageResponse, status_code=201)
async def create_package(
    data: SubmittalPackageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a submittal package."""
    svc = _get_service(db, current_user)
    return svc.create_package(data)


@router.delete("/submittal-packages/{package_id}", status_code=204)
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a submittal package."""
    svc = _get_service(db, current_user)
    if not svc.delete_package(package_id):
        raise HTTPException(status_code=404, detail="Package not found")


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@router.get("/submittal-types", response_model=list[SubmittalTypeResponse])
async def list_types(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List submittal types."""
    svc = _get_service(db, current_user)
    return svc.list_types()


@router.post("/submittal-types", response_model=SubmittalTypeResponse, status_code=201)
async def create_type(
    data: SubmittalTypeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a submittal type."""
    svc = _get_service(db, current_user)
    return svc.create_type(data)


@router.delete("/submittal-types/{type_id}", status_code=204)
async def delete_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a submittal type."""
    svc = _get_service(db, current_user)
    if not svc.delete_type(type_id):
        raise HTTPException(status_code=404, detail="Type not found")


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

@router.get("/submittal-labels", response_model=list[SubmittalLabelResponse])
async def list_labels(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List submittal labels."""
    svc = _get_service(db, current_user)
    return svc.list_labels()


@router.post("/submittal-labels", response_model=SubmittalLabelResponse, status_code=201)
async def create_label(
    data: SubmittalLabelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a submittal label."""
    svc = _get_service(db, current_user)
    return svc.create_label(data)


@router.delete("/submittal-labels/{label_id}", status_code=204)
async def delete_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a submittal label."""
    svc = _get_service(db, current_user)
    if not svc.delete_label(label_id):
        raise HTTPException(status_code=404, detail="Label not found")


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

class AttachDocumentBody(BaseModel):
    document_id: int


@router.get("/submittals/{submittal_id}/attachments")
async def list_submittal_attachments(
    submittal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List documents attached to a submittal."""
    company_id = get_effective_company_id(current_user, db)
    stmt = select(agcm_entity_attachments).where(
        agcm_entity_attachments.c.entity_type == "submittal",
        agcm_entity_attachments.c.entity_id == submittal_id,
        agcm_entity_attachments.c.company_id == company_id,
    )
    rows = db.execute(stmt).mappings().all()
    return [dict(r) for r in rows]


@router.post("/submittals/{submittal_id}/attachments", status_code=201)
async def attach_document_to_submittal(
    submittal_id: int,
    body: AttachDocumentBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Attach a document to a submittal."""
    company_id = get_effective_company_id(current_user, db)
    stmt = insert(agcm_entity_attachments).values(
        entity_type="submittal",
        entity_id=submittal_id,
        document_id=body.document_id,
        company_id=company_id,
    )
    db.execute(stmt)
    db.commit()
    return {"message": "Document attached", "document_id": body.document_id, "submittal_id": submittal_id}


@router.delete("/submittals/{submittal_id}/attachments/{document_id}", status_code=204)
async def detach_document_from_submittal(
    submittal_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Detach a document from a submittal."""
    company_id = get_effective_company_id(current_user, db)
    stmt = delete(agcm_entity_attachments).where(
        agcm_entity_attachments.c.entity_type == "submittal",
        agcm_entity_attachments.c.entity_id == submittal_id,
        agcm_entity_attachments.c.document_id == document_id,
        agcm_entity_attachments.c.company_id == company_id,
    )
    db.execute(stmt)
    db.commit()
