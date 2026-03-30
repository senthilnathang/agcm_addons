"""API routes for Estimates, Groups, Line Items, and Markups."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_estimate.schemas.estimate import (
    EstimateCreate, EstimateUpdate, EstimateResponse,
    EstimateGroupCreate, EstimateGroupUpdate, EstimateGroupResponse,
    EstimateLineItemCreate, EstimateLineItemUpdate, EstimateLineItemResponse,
    EstimateMarkupCreate, EstimateMarkupUpdate, EstimateMarkupResponse,
    AddAssemblyRequest,
)
from addons.agcm_estimate.services.estimate_service import EstimateService

router = APIRouter()


def _get_service(db: Session, current_user) -> EstimateService:
    company_id = get_effective_company_id(current_user, db)
    return EstimateService(db=db, company_id=company_id, user_id=current_user.id)


# =============================================================================
# ESTIMATES
# =============================================================================

@router.get("/estimates", response_model=None)
async def list_estimates(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List estimates with optional project and status filters."""
    svc = _get_service(db, current_user)
    return svc.list_estimates(
        project_id=project_id, status=status, page=page, page_size=page_size,
    )


@router.get("/estimates/{estimate_id}", response_model=None)
async def get_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get full estimate detail with groups, line items, markups, summary."""
    svc = _get_service(db, current_user)
    detail = svc.get_estimate_detail(estimate_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return detail


@router.post("/estimates", response_model=None, status_code=201)
async def create_estimate(
    data: EstimateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new estimate."""
    svc = _get_service(db, current_user)
    estimate = svc.create_estimate(data)
    return EstimateResponse.model_validate(estimate).model_dump()


@router.put("/estimates/{estimate_id}", response_model=None)
async def update_estimate(
    estimate_id: int,
    data: EstimateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an estimate."""
    svc = _get_service(db, current_user)
    estimate = svc.update_estimate(estimate_id, data)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse.model_validate(estimate).model_dump()


@router.delete("/estimates/{estimate_id}", status_code=204)
async def delete_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an estimate."""
    svc = _get_service(db, current_user)
    if not svc.delete_estimate(estimate_id):
        raise HTTPException(status_code=404, detail="Estimate not found")


@router.post("/estimates/{estimate_id}/recalculate", response_model=None)
async def recalculate_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Recalculate all estimate totals from line items and markups."""
    svc = _get_service(db, current_user)
    estimate = svc.recalculate_estimate(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse.model_validate(estimate).model_dump()


@router.post("/estimates/{estimate_id}/create-version", response_model=None)
async def create_version(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new version from the current estimate."""
    svc = _get_service(db, current_user)
    new_estimate = svc.create_version(estimate_id)
    if not new_estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse.model_validate(new_estimate).model_dump()


@router.post("/estimates/{estimate_id}/send-to-budget", response_model=None)
async def send_to_budget(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate budget lines from estimate line items grouped by cost code."""
    svc = _get_service(db, current_user)
    result = svc.send_to_budget(estimate_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Failed"))
    return result


@router.post("/estimates/{estimate_id}/approve", response_model=None)
async def approve_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve an estimate."""
    svc = _get_service(db, current_user)
    estimate = svc.approve_estimate(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse.model_validate(estimate).model_dump()


@router.post("/estimates/{estimate_id}/add-assembly", response_model=None)
async def add_assembly_to_estimate(
    estimate_id: int,
    data: AddAssemblyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add an assembly's items to an estimate group."""
    svc = _get_service(db, current_user)
    items = svc.add_assembly_to_estimate(
        estimate_id=estimate_id,
        group_id=data.group_id,
        assembly_id=data.assembly_id,
        quantity_multiplier=data.quantity_multiplier,
    )
    return [EstimateLineItemResponse.model_validate(i).model_dump() for i in items]


# =============================================================================
# ESTIMATE GROUPS
# =============================================================================

@router.post("/estimate-groups", response_model=None, status_code=201)
async def create_group(
    data: EstimateGroupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new estimate group."""
    svc = _get_service(db, current_user)
    group = svc.create_group(data)
    return EstimateGroupResponse.model_validate(group).model_dump()


@router.put("/estimate-groups/{group_id}", response_model=None)
async def update_group(
    group_id: int,
    data: EstimateGroupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an estimate group."""
    svc = _get_service(db, current_user)
    group = svc.update_group(group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return EstimateGroupResponse.model_validate(group).model_dump()


@router.delete("/estimate-groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an estimate group."""
    svc = _get_service(db, current_user)
    result = svc.delete_group(group_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Group not found")


# =============================================================================
# ESTIMATE LINE ITEMS
# =============================================================================

@router.post("/estimate-line-items", response_model=None, status_code=201)
async def create_line_item(
    data: EstimateLineItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new estimate line item (auto-recalculates estimate)."""
    svc = _get_service(db, current_user)
    li = svc.create_line_item(data)
    return EstimateLineItemResponse.model_validate(li).model_dump()


@router.put("/estimate-line-items/{item_id}", response_model=None)
async def update_line_item(
    item_id: int,
    data: EstimateLineItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an estimate line item (auto-recalculates estimate)."""
    svc = _get_service(db, current_user)
    li = svc.update_line_item(item_id, data)
    if not li:
        raise HTTPException(status_code=404, detail="Line item not found")
    return EstimateLineItemResponse.model_validate(li).model_dump()


@router.delete("/estimate-line-items/{item_id}", status_code=204)
async def delete_line_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an estimate line item (auto-recalculates estimate)."""
    svc = _get_service(db, current_user)
    result = svc.delete_line_item(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Line item not found")


# =============================================================================
# ESTIMATE MARKUPS
# =============================================================================

@router.post("/estimate-markups", response_model=None, status_code=201)
async def create_markup(
    data: EstimateMarkupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a markup to an estimate."""
    svc = _get_service(db, current_user)
    markup = svc.create_markup(data)
    return EstimateMarkupResponse.model_validate(markup).model_dump()


@router.put("/estimate-markups/{markup_id}", response_model=None)
async def update_markup(
    markup_id: int,
    data: EstimateMarkupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a markup."""
    svc = _get_service(db, current_user)
    markup = svc.update_markup(markup_id, data)
    if not markup:
        raise HTTPException(status_code=404, detail="Markup not found")
    return EstimateMarkupResponse.model_validate(markup).model_dump()


@router.delete("/estimate-markups/{markup_id}", status_code=204)
async def delete_markup(
    markup_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a markup."""
    svc = _get_service(db, current_user)
    result = svc.delete_markup(markup_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Markup not found")
