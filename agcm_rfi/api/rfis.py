"""API routes for RFIs"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import insert, delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id
from addons.agcm.models.entity_attachment import agcm_entity_attachments

from addons.agcm_rfi.schemas.rfi import (
    RFICreate,
    RFIUpdate,
    RFIResponseSchema,
    RFIDetail,
    RFIResponseCreate,
    RFIResponseUpdate,
    RFIResponseResponseSchema,
)
from addons.agcm_rfi.services.rfi_service import RFIService

router = APIRouter()


def _get_service(db: Session, current_user) -> RFIService:
    company_id = get_effective_company_id(current_user, db)
    return RFIService(db, company_id, current_user.id)


@router.get("/rfis")
async def list_rfis(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_rfis(project_id, status, priority, search, page, page_size)
    result["items"] = [
        RFIResponseSchema.model_validate(i).model_dump() for i in result["items"]
    ]
    return result


@router.get("/rfis/{rfi_id}", response_model=RFIDetail)
async def get_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    detail = svc.get_rfi_detail(rfi_id)
    if not detail:
        raise HTTPException(status_code=404, detail="RFI not found")
    return detail


@router.post("/rfis", response_model=RFIResponseSchema, status_code=201)
async def create_rfi(
    data: RFICreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    rfi = svc.create_rfi(data)
    try:
        from addons.agcm.services.realtime_events import agcm_realtime

        await agcm_realtime.rfi_created(db, rfi)
    except Exception:
        pass
    return rfi


@router.put("/rfis/{rfi_id}", response_model=RFIResponseSchema)
async def update_rfi(
    rfi_id: int,
    data: RFIUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_rfi(rfi_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="RFI not found")
    return result


@router.delete("/rfis/{rfi_id}", status_code=204)
async def delete_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_rfi(rfi_id):
        raise HTTPException(status_code=404, detail="RFI not found")


@router.post("/rfis/{rfi_id}/restore", response_model=RFIResponseSchema)
async def restore_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.restore_rfi(rfi_id)
    if not result:
        raise HTTPException(status_code=404, detail="RFI not found or not deleted")
    return result


@router.post("/rfis/{rfi_id}/close", response_model=RFIResponseSchema)
async def close_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.close_rfi(rfi_id)
    if not result:
        raise HTTPException(status_code=404, detail="RFI not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime

        await agcm_realtime.rfi_closed(db, result)
    except Exception:
        pass
    return result


@router.post("/rfis/{rfi_id}/reopen", response_model=RFIResponseSchema)
async def reopen_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.reopen_rfi(rfi_id)
    if not result:
        raise HTTPException(status_code=404, detail="RFI not found")
    return result


@router.post("/rfis/{rfi_id}/create-change-order")
async def create_change_order_from_rfi(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a draft Change Order pre-populated from an RFI's cost/schedule impact."""
    svc = _get_service(db, current_user)
    result = svc.create_change_order_from_rfi(rfi_id)
    if result is None:
        raise HTTPException(status_code=404, detail="RFI not found or change order module unavailable")
    return result


# --- Responses ---


@router.post(
    "/rfis/{rfi_id}/responses",
    response_model=RFIResponseResponseSchema,
    status_code=201,
)
async def create_rfi_response(
    rfi_id: int,
    data: RFIResponseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.create_response(rfi_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="RFI not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime

        rfi = svc.get_rfi(rfi_id)
        if rfi:
            await agcm_realtime.rfi_response_created(db, rfi, result)
    except Exception:
        pass
    return result


# --- Attachments ---


class AttachDocumentBody(BaseModel):
    document_id: int


@router.get("/rfis/{rfi_id}/attachments")
async def list_rfi_attachments(
    rfi_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List documents attached to an RFI."""
    company_id = get_effective_company_id(current_user, db)
    stmt = select(agcm_entity_attachments).where(
        agcm_entity_attachments.c.entity_type == "rfi",
        agcm_entity_attachments.c.entity_id == rfi_id,
        agcm_entity_attachments.c.company_id == company_id,
    )
    rows = db.execute(stmt).mappings().all()
    return [dict(r) for r in rows]


@router.post("/rfis/{rfi_id}/attachments", status_code=201)
async def attach_document_to_rfi(
    rfi_id: int,
    body: AttachDocumentBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Attach a document to an RFI."""
    company_id = get_effective_company_id(current_user, db)
    stmt = insert(agcm_entity_attachments).values(
        entity_type="rfi",
        entity_id=rfi_id,
        document_id=body.document_id,
        company_id=company_id,
    )
    db.execute(stmt)
    db.commit()
    return {
        "message": "Document attached",
        "document_id": body.document_id,
        "rfi_id": rfi_id,
    }


@router.delete("/rfis/{rfi_id}/attachments/{document_id}", status_code=204)
async def detach_document_from_rfi(
    rfi_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Detach a document from an RFI."""
    company_id = get_effective_company_id(current_user, db)
    stmt = delete(agcm_entity_attachments).where(
        agcm_entity_attachments.c.entity_type == "rfi",
        agcm_entity_attachments.c.entity_id == rfi_id,
        agcm_entity_attachments.c.document_id == document_id,
        agcm_entity_attachments.c.company_id == company_id,
    )
    db.execute(stmt)
    db.commit()


@router.put("/rfi-responses/{response_id}", response_model=RFIResponseResponseSchema)
async def update_rfi_response(
    response_id: int,
    data: RFIResponseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_response(response_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Response not found")
    return result
