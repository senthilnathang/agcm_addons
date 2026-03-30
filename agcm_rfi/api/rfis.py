"""API routes for RFIs"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_rfi.schemas.rfi import (
    RFICreate, RFIUpdate, RFIResponseSchema, RFIDetail,
    RFIResponseCreate, RFIResponseUpdate, RFIResponseResponseSchema,
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
    result["items"] = [RFIResponseSchema.model_validate(i).model_dump() for i in result["items"]]
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


# --- Responses ---

@router.post("/rfis/{rfi_id}/responses", response_model=RFIResponseResponseSchema, status_code=201)
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
