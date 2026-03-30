"""API routes for RFI Labels"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_rfi.schemas.rfi import RFILabelCreate, RFILabelResponse
from addons.agcm_rfi.services.rfi_service import RFIService

router = APIRouter()


@router.get("/rfi-labels", response_model=list[RFILabelResponse])
async def list_labels(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    svc = RFIService(db, company_id, current_user.id)
    return svc.list_labels()


@router.post("/rfi-labels", response_model=RFILabelResponse, status_code=201)
async def create_label(
    data: RFILabelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    svc = RFIService(db, company_id, current_user.id)
    return svc.create_label(data.name, data.color)


@router.delete("/rfi-labels/{label_id}", status_code=204)
async def delete_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    svc = RFIService(db, company_id, current_user.id)
    if not svc.delete_label(label_id):
        raise HTTPException(status_code=404, detail="Label not found")
