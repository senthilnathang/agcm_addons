"""API routes for Vendor Bills."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_procurement.schemas.procurement import (
    VendorBillCreate, VendorBillUpdate, VendorBillResponse, VendorBillDetail,
    VendorBillLineCreate, VendorBillLineUpdate, VendorBillLineResponse,
    VendorBillPaymentCreate, VendorBillPaymentResponse,
)
from addons.agcm_procurement.services.procurement_service import ProcurementService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProcurementService:
    company_id = get_effective_company_id(current_user, db)
    return ProcurementService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/vendor-bills", response_model=None)
async def list_vendor_bills(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    record_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List vendor bills with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_vendor_bills(
        page=page, page_size=page_size,
        project_id=project_id, status=status,
        record_type=record_type, search=search,
    )


@router.get("/vendor-bills/{bill_id}", response_model=None)
async def get_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get vendor bill detail with lines and payments."""
    svc = _get_service(db, current_user)
    detail = svc.get_vendor_bill_detail(bill_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return detail


@router.post("/vendor-bills", response_model=None, status_code=201)
async def create_vendor_bill(
    data: VendorBillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new vendor bill with optional lines."""
    svc = _get_service(db, current_user)
    bill = svc.create_vendor_bill(data)
    return VendorBillResponse.model_validate(bill).model_dump()


@router.put("/vendor-bills/{bill_id}", response_model=None)
async def update_vendor_bill(
    bill_id: int,
    data: VendorBillUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a vendor bill."""
    svc = _get_service(db, current_user)
    bill = svc.update_vendor_bill(bill_id, data)
    if not bill:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return VendorBillResponse.model_validate(bill).model_dump()


@router.delete("/vendor-bills/{bill_id}", status_code=204)
async def delete_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a vendor bill."""
    svc = _get_service(db, current_user)
    if not svc.delete_vendor_bill(bill_id):
        raise HTTPException(status_code=404, detail="Vendor bill not found")


@router.post("/vendor-bills/{bill_id}/approve", response_model=None)
async def approve_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a vendor bill."""
    svc = _get_service(db, current_user)
    bill = svc.approve_vendor_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return VendorBillResponse.model_validate(bill).model_dump()


@router.post("/vendor-bills/{bill_id}/record-payment", response_model=None)
async def record_payment(
    bill_id: int,
    data: VendorBillPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a payment against a vendor bill."""
    svc = _get_service(db, current_user)
    payment = svc.record_payment(bill_id, data)
    if not payment:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return VendorBillPaymentResponse.model_validate(payment).model_dump()


@router.post("/vendor-bills/{bill_id}/check-duplicate", response_model=None)
async def check_duplicate(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Check if the bill is a potential duplicate."""
    svc = _get_service(db, current_user)
    bill = svc.get_vendor_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Vendor bill not found")

    duplicates = svc.check_duplicate_bill(
        vendor_name=bill.vendor_name,
        vendor_invoice_ref=bill.vendor_invoice_ref,
        project_id=bill.project_id,
        exclude_id=bill_id,
    )

    if duplicates:
        bill.duplicate_flag = True
        bill.duplicate_of_id = duplicates[0].id
        svc.db.commit()

    return {
        "bill_id": bill_id,
        "is_duplicate": len(duplicates) > 0,
        "duplicate_count": len(duplicates),
        "duplicates": [
            {
                "id": d.id,
                "sequence_name": d.sequence_name,
                "bill_number": d.bill_number,
                "vendor_invoice_ref": d.vendor_invoice_ref,
                "total_amount": d.total_amount,
            }
            for d in duplicates
        ],
    }


@router.post("/vendor-bills/{bill_id}/auto-match-po", response_model=None)
async def auto_match_po(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Try to auto-match a bill to a purchase order."""
    svc = _get_service(db, current_user)
    result = svc.auto_match_po(bill_id)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return result


# ---- Bill Lines ----

@router.post("/bill-lines", response_model=None, status_code=201)
async def create_bill_line(
    data: VendorBillLineCreate,
    bill_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a line to a vendor bill."""
    svc = _get_service(db, current_user)
    line = svc.create_bill_line(data, bill_id)
    if not line:
        raise HTTPException(status_code=404, detail="Vendor bill not found")
    return VendorBillLineResponse.model_validate(line).model_dump()


@router.put("/bill-lines/{line_id}", response_model=None)
async def update_bill_line(
    line_id: int,
    data: VendorBillLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a bill line."""
    svc = _get_service(db, current_user)
    line = svc.update_bill_line(line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Bill line not found")
    return VendorBillLineResponse.model_validate(line).model_dump()


@router.delete("/bill-lines/{line_id}", status_code=204)
async def delete_bill_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a bill line."""
    svc = _get_service(db, current_user)
    if not svc.delete_bill_line(line_id):
        raise HTTPException(status_code=404, detail="Bill line not found")
