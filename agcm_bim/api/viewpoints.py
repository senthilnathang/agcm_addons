"""API routes for BIM Viewpoints"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_bim.schemas.bim import (
    BIMViewpointCreate, BIMViewpointUpdate, BIMViewpointResponse,
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


@router.post("/viewpoints", response_model=BIMViewpointResponse, status_code=201)
async def create_viewpoint(
    data: BIMViewpointCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_viewpoint(data)


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
