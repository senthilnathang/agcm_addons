"""API routes for Bills"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    BillCreate,
    BillUpdate,
    BillResponse,
    BillDetail,
    BillLineCreate,
    BillLineUpdate,
    BillLineResponse,
    RecordPayment,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/bills")
async def list_bills(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List bills with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_bills(project_id, status, page, page_size)
    result["items"] = [BillResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get bill details."""
    svc = _get_service(db, current_user)
    bill = svc.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.post("/bills", response_model=BillResponse, status_code=201)
async def create_bill(
    data: BillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new bill."""
    svc = _get_service(db, current_user)
    return svc.create_bill(data)


@router.put("/bills/{bill_id}", response_model=BillResponse)
async def update_bill(
    bill_id: int,
    data: BillUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a bill."""
    svc = _get_service(db, current_user)
    result = svc.update_bill(bill_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Bill not found")
    return result


@router.delete("/bills/{bill_id}", status_code=204)
async def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a bill."""
    svc = _get_service(db, current_user)
    if not svc.delete_bill(bill_id):
        raise HTTPException(status_code=404, detail="Bill not found")


@router.get("/bills/{bill_id}/detail", response_model=BillDetail)
async def get_bill_detail(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get bill with line items."""
    svc = _get_service(db, current_user)
    result = svc.get_bill_detail(bill_id)
    if not result:
        raise HTTPException(status_code=404, detail="Bill not found")
    return result


@router.post("/bill-lines", response_model=BillLineResponse, status_code=201)
async def add_bill_line(
    data: BillLineCreate,
    bill_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.add_bill_line(bill_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Bill not found")
    return result


@router.put("/bill-lines/{line_id}", response_model=BillLineResponse)
async def update_bill_line(
    line_id: int,
    data: BillLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_bill_line(line_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Line not found")
    return result


@router.delete("/bill-lines/{line_id}", status_code=204)
async def delete_bill_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_bill_line(line_id):
        raise HTTPException(status_code=404, detail="Line not found")


@router.post("/bills/{bill_id}/record-payment", response_model=BillResponse)
async def record_bill_payment(
    bill_id: int,
    data: RecordPayment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a payment against a bill."""
    svc = _get_service(db, current_user)
    result = svc.record_bill_payment(bill_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Bill not found")
    return result
