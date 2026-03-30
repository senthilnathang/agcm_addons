"""API routes for Purchase Orders."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_procurement.schemas.procurement import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, PurchaseOrderDetail,
    PurchaseOrderLineCreate, PurchaseOrderLineUpdate, PurchaseOrderLineResponse,
    ReceiveDeliveryRequest, CreateFromEstimateRequest,
)
from addons.agcm_procurement.services.procurement_service import ProcurementService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProcurementService:
    company_id = get_effective_company_id(current_user, db)
    return ProcurementService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/purchase-orders", response_model=None)
async def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List purchase orders with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_purchase_orders(
        page=page, page_size=page_size,
        project_id=project_id, status=status, search=search,
    )


@router.get("/purchase-orders/{po_id}", response_model=None)
async def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get purchase order detail with lines."""
    svc = _get_service(db, current_user)
    detail = svc.get_purchase_order_detail(po_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return detail


@router.post("/purchase-orders", response_model=None, status_code=201)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new purchase order with optional lines."""
    svc = _get_service(db, current_user)
    po = svc.create_purchase_order(data)
    return PurchaseOrderResponse.model_validate(po).model_dump()


@router.put("/purchase-orders/{po_id}", response_model=None)
async def update_purchase_order(
    po_id: int,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a purchase order."""
    svc = _get_service(db, current_user)
    po = svc.update_purchase_order(po_id, data)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return PurchaseOrderResponse.model_validate(po).model_dump()


@router.delete("/purchase-orders/{po_id}", status_code=204)
async def delete_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a purchase order."""
    svc = _get_service(db, current_user)
    if not svc.delete_purchase_order(po_id):
        raise HTTPException(status_code=404, detail="Purchase order not found")


@router.post("/purchase-orders/{po_id}/approve", response_model=None)
async def approve_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a purchase order."""
    svc = _get_service(db, current_user)
    po = svc.approve_po(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return PurchaseOrderResponse.model_validate(po).model_dump()


@router.post("/purchase-orders/{po_id}/receive", response_model=None)
async def receive_delivery(
    po_id: int,
    data: ReceiveDeliveryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update received quantities on PO lines."""
    svc = _get_service(db, current_user)
    po = svc.receive_delivery(po_id, data.line_updates)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return PurchaseOrderResponse.model_validate(po).model_dump()


@router.post("/purchase-orders/from-estimate", response_model=None, status_code=201)
async def create_po_from_estimate(
    data: CreateFromEstimateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a purchase order from an estimate's line items."""
    svc = _get_service(db, current_user)
    po = svc.create_po_from_estimate(data.estimate_id, data.vendor_name)
    if not po:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return PurchaseOrderResponse.model_validate(po).model_dump()


# ---- PO Lines ----

@router.post("/po-lines", response_model=None, status_code=201)
async def create_po_line(
    data: PurchaseOrderLineCreate,
    po_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a line to a purchase order."""
    svc = _get_service(db, current_user)
    line = svc.create_po_line(data, po_id)
    if not line:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return PurchaseOrderLineResponse.model_validate(line).model_dump()


@router.put("/po-lines/{line_id}", response_model=None)
async def update_po_line(
    line_id: int,
    data: PurchaseOrderLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a PO line."""
    svc = _get_service(db, current_user)
    line = svc.update_po_line(line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="PO line not found")
    return PurchaseOrderLineResponse.model_validate(line).model_dump()


@router.delete("/po-lines/{line_id}", status_code=204)
async def delete_po_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a PO line."""
    svc = _get_service(db, current_user)
    if not svc.delete_po_line(line_id):
        raise HTTPException(status_code=404, detail="PO line not found")
