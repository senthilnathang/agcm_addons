"""API routes for BIM Viewpoints — Phase 3: Collaboration features"""

import base64
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_bim.schemas.bim import (
    BIMViewpointCreate, BIMViewpointUpdate, BIMViewpointResponse,
    BIMViewpointLinkEntity,
)
from addons.agcm_bim.services.bim_service import BIMService

router = APIRouter()


def _get_service(db: Session, current_user) -> BIMService:
    company_id = get_effective_company_id(current_user, db)
    return BIMService(db, company_id, current_user.id)


@router.get("/viewpoints")
async def list_viewpoints(
    model_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_viewpoints(model_id, entity_type, entity_id, page, page_size)
    result["items"] = [BIMViewpointResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/viewpoints/by-entity")
async def get_viewpoints_by_entity(
    entity_type: str = Query(..., description="Entity type: rfi, issue, clash, submittal"),
    entity_id: int = Query(..., description="Entity ID"),
    page: int = 1,
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all viewpoints linked to a specific entity."""
    svc = _get_service(db, current_user)
    result = svc.list_viewpoints(
        model_id=None,
        entity_type=entity_type,
        entity_id=entity_id,
        page=page,
        page_size=page_size,
    )
    result["items"] = [BIMViewpointResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/viewpoints/{viewpoint_id}", response_model=BIMViewpointResponse)
async def get_viewpoint(
    viewpoint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    vp = svc.get_viewpoint(viewpoint_id)
    if not vp:
        raise HTTPException(status_code=404, detail="Viewpoint not found")
    return vp


@router.get("/viewpoints/{viewpoint_id}/snapshot")
async def get_viewpoint_snapshot(
    viewpoint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Serve the snapshot image as PNG bytes."""
    svc = _get_service(db, current_user)
    vp = svc.get_viewpoint(viewpoint_id)
    if not vp:
        raise HTTPException(status_code=404, detail="Viewpoint not found")
    if not vp.snapshot_base64:
        raise HTTPException(status_code=404, detail="No snapshot available")
    # Strip data URL prefix if present
    b64 = vp.snapshot_base64
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    try:
        img_bytes = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid snapshot data")
    return Response(content=img_bytes, media_type="image/png")


@router.post("/viewpoints", response_model=BIMViewpointResponse, status_code=201)
async def create_viewpoint(
    data: BIMViewpointCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_viewpoint(data)


@router.post("/viewpoints/{viewpoint_id}/link", response_model=BIMViewpointResponse)
async def link_viewpoint_to_entity(
    viewpoint_id: int,
    data: BIMViewpointLinkEntity,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Link a viewpoint to an entity (RFI, Issue, etc.)."""
    svc = _get_service(db, current_user)
    result = svc.link_viewpoint_to_entity(viewpoint_id, data.entity_type, data.entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Viewpoint not found")
    return result


@router.put("/viewpoints/{viewpoint_id}", response_model=BIMViewpointResponse)
async def update_viewpoint(
    viewpoint_id: int,
    data: BIMViewpointUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_viewpoint(viewpoint_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Viewpoint not found")
    return result


@router.delete("/viewpoints/{viewpoint_id}", status_code=204)
async def delete_viewpoint(
    viewpoint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_viewpoint(viewpoint_id):
        raise HTTPException(status_code=404, detail="Viewpoint not found")
