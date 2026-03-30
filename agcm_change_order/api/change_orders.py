"""API routes for Change Orders"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_change_order.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderUpdate,
    ChangeOrderResponse,
    ChangeOrderDetail,
    ChangeOrderLineCreate,
    ChangeOrderLineUpdate,
    ChangeOrderLineResponse,
)
from addons.agcm_change_order.services.change_order_service import ChangeOrderService

router = APIRouter()


def _get_service(db: Session, current_user) -> ChangeOrderService:
    company_id = get_effective_company_id(current_user, db)
    return ChangeOrderService(db, company_id, current_user.id)


@router.get("/change-orders")
async def list_change_orders(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List change orders with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_change_orders(project_id, status, search, page, page_size)
    result["items"] = [ChangeOrderResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/change-orders/{co_id}", response_model=ChangeOrderDetail)
async def get_change_order(
    co_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get change order details with line items."""
    svc = _get_service(db, current_user)
    detail = svc.get_change_order_detail(co_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Change order not found")
    return detail


@router.post("/change-orders", response_model=ChangeOrderResponse, status_code=201)
async def create_change_order(
    data: ChangeOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new change order."""
    svc = _get_service(db, current_user)
    co = svc.create_change_order(data)
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.change_order_created(db, co)
    except Exception:
        pass
    return co


@router.put("/change-orders/{co_id}", response_model=ChangeOrderResponse)
async def update_change_order(
    co_id: int,
    data: ChangeOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a change order."""
    svc = _get_service(db, current_user)
    result = svc.update_change_order(co_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Change order not found")
    return result


@router.delete("/change-orders/{co_id}", status_code=204)
async def delete_change_order(
    co_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a change order."""
    svc = _get_service(db, current_user)
    if not svc.delete_change_order(co_id):
        raise HTTPException(status_code=404, detail="Change order not found")


@router.post("/change-orders/{co_id}/approve", response_model=ChangeOrderResponse)
async def approve_change_order(
    co_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a change order."""
    svc = _get_service(db, current_user)
    result = svc.approve_change_order(co_id)
    if not result:
        raise HTTPException(status_code=404, detail="Change order not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.change_order_status_changed(db, result, "pending", "approved")
    except Exception:
        pass
    return result


@router.post("/change-orders/{co_id}/reject", response_model=ChangeOrderResponse)
async def reject_change_order(
    co_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject a change order."""
    svc = _get_service(db, current_user)
    result = svc.reject_change_order(co_id)
    if not result:
        raise HTTPException(status_code=404, detail="Change order not found")
    return result


# --- Line Item Endpoints ---

@router.post("/change-order-lines", response_model=ChangeOrderLineResponse, status_code=201)
async def create_line(
    data: ChangeOrderLineCreate,
    change_order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a line item to a change order."""
    svc = _get_service(db, current_user)
    result = svc.add_line(change_order_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Change order not found")
    return result


@router.put("/change-order-lines/{line_id}", response_model=ChangeOrderLineResponse)
async def update_line(
    line_id: int,
    data: ChangeOrderLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a change order line item."""
    svc = _get_service(db, current_user)
    result = svc.update_line(line_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Line item not found")
    return result


@router.delete("/change-order-lines/{line_id}", status_code=204)
async def delete_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a change order line item."""
    svc = _get_service(db, current_user)
    if not svc.delete_line(line_id):
        raise HTTPException(status_code=404, detail="Line item not found")
