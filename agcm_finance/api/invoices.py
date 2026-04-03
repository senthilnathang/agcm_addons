"""API routes for Invoices"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetail,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
    RecordPayment,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/invoices")
async def list_invoices(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List invoices with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_invoices(project_id, status, page, page_size)
    result["items"] = [InvoiceResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get invoice details."""
    svc = _get_service(db, current_user)
    inv = svc.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new invoice."""
    svc = _get_service(db, current_user)
    return svc.create_invoice(data)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an invoice."""
    svc = _get_service(db, current_user)
    result = svc.update_invoice(invoice_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an invoice."""
    svc = _get_service(db, current_user)
    if not svc.delete_invoice(invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")


@router.get("/invoices/{invoice_id}/detail", response_model=InvoiceDetail)
async def get_invoice_detail(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get invoice with line items."""
    svc = _get_service(db, current_user)
    result = svc.get_invoice_detail(invoice_id)
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result


@router.post("/invoice-lines", response_model=InvoiceLineResponse, status_code=201)
async def add_invoice_line(
    data: InvoiceLineCreate,
    invoice_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.add_invoice_line(invoice_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result


@router.put("/invoice-lines/{line_id}", response_model=InvoiceLineResponse)
async def update_invoice_line(
    line_id: int,
    data: InvoiceLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_invoice_line(line_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Line not found")
    return result


@router.delete("/invoice-lines/{line_id}", status_code=204)
async def delete_invoice_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_invoice_line(line_id):
        raise HTTPException(status_code=404, detail="Line not found")


@router.post("/invoices/{invoice_id}/record-payment", response_model=InvoiceResponse)
async def record_invoice_payment(
    invoice_id: int,
    data: RecordPayment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a payment against an invoice."""
    svc = _get_service(db, current_user)
    result = svc.record_invoice_payment(invoice_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result
