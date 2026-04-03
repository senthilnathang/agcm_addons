"""API routes for Vendor directory."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_contact.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from addons.agcm_contact.services.vendor_service import VendorService

router = APIRouter()


def _get_service(db: Session, current_user) -> VendorService:
    company_id = get_effective_company_id(current_user, db)
    return VendorService(db, company_id, current_user.id)


@router.get("/vendors")
async def list_vendors(
    vendor_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_vendors(vendor_type, search, is_active, page, page_size)
    result["items"] = [VendorResponse.model_validate(v).model_dump() for v in result["items"]]
    return result


@router.get("/vendors/search")
async def search_vendors(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Quick search for autocomplete dropdowns."""
    svc = _get_service(db, current_user)
    results = svc.search_vendors(q, limit)
    return [{"id": v.id, "name": v.name, "vendor_type": v.vendor_type} for v in results]


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    vendor = svc.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/vendors", response_model=VendorResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_vendor(data)


@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_vendor(vendor_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return result


@router.delete("/vendors/{vendor_id}", status_code=204)
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_vendor(vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
