"""API routes for Cost Catalogs and Cost Items."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_estimate.schemas.estimate import (
    CostCatalogCreate, CostCatalogUpdate, CostCatalogResponse,
    CostItemCreate, CostItemUpdate, CostItemResponse,
)
from addons.agcm_estimate.services.estimate_service import EstimateService

router = APIRouter()


def _get_service(db: Session, current_user) -> EstimateService:
    company_id = get_effective_company_id(current_user, db)
    return EstimateService(db=db, company_id=company_id, user_id=current_user.id)


# =============================================================================
# COST CATALOGS
# =============================================================================

@router.get("/catalogs", response_model=None)
async def list_catalogs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List cost catalogs."""
    svc = _get_service(db, current_user)
    return svc.list_catalogs(page=page, page_size=page_size)


@router.post("/catalogs", response_model=None, status_code=201)
async def create_catalog(
    data: CostCatalogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new cost catalog."""
    svc = _get_service(db, current_user)
    catalog = svc.create_catalog(data)
    return CostCatalogResponse.model_validate(catalog).model_dump()


@router.put("/catalogs/{catalog_id}", response_model=None)
async def update_catalog(
    catalog_id: int,
    data: CostCatalogUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a cost catalog."""
    svc = _get_service(db, current_user)
    catalog = svc.update_catalog(catalog_id, data)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return CostCatalogResponse.model_validate(catalog).model_dump()


@router.delete("/catalogs/{catalog_id}", status_code=204)
async def delete_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a cost catalog."""
    svc = _get_service(db, current_user)
    if not svc.delete_catalog(catalog_id):
        raise HTTPException(status_code=404, detail="Catalog not found")


# =============================================================================
# COST ITEMS
# =============================================================================

@router.get("/cost-items", response_model=None)
async def list_cost_items(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    catalog_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List cost items with optional filters."""
    svc = _get_service(db, current_user)
    return svc.list_cost_items(
        catalog_id=catalog_id, item_type=item_type, search=search,
        page=page, page_size=page_size,
    )


@router.post("/cost-items", response_model=None, status_code=201)
async def create_cost_item(
    data: CostItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new cost item."""
    svc = _get_service(db, current_user)
    item = svc.create_cost_item(data)
    return CostItemResponse.model_validate(item).model_dump()


@router.put("/cost-items/{item_id}", response_model=None)
async def update_cost_item(
    item_id: int,
    data: CostItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a cost item."""
    svc = _get_service(db, current_user)
    item = svc.update_cost_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Cost item not found")
    return CostItemResponse.model_validate(item).model_dump()


@router.delete("/cost-items/{item_id}", status_code=204)
async def delete_cost_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a cost item."""
    svc = _get_service(db, current_user)
    if not svc.delete_cost_item(item_id):
        raise HTTPException(status_code=404, detail="Cost item not found")
