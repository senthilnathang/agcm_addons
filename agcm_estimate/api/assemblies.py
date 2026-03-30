"""API routes for Assemblies."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_estimate.schemas.estimate import (
    AssemblyCreate, AssemblyUpdate, AssemblyResponse, AssemblyDetail,
    AssemblyItemCreate, AssemblyItemUpdate, AssemblyItemResponse,
)
from addons.agcm_estimate.services.estimate_service import EstimateService

router = APIRouter()


def _get_service(db: Session, current_user) -> EstimateService:
    company_id = get_effective_company_id(current_user, db)
    return EstimateService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/assemblies", response_model=None)
async def list_assemblies(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    category: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List assemblies with optional category filter."""
    svc = _get_service(db, current_user)
    return svc.list_assemblies(category=category, page=page, page_size=page_size)


@router.get("/assemblies/{assembly_id}", response_model=None)
async def get_assembly(
    assembly_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get assembly detail with items."""
    svc = _get_service(db, current_user)
    assembly = svc.get_assembly(assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    return AssemblyDetail.model_validate(assembly).model_dump()


@router.post("/assemblies", response_model=None, status_code=201)
async def create_assembly(
    data: AssemblyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new assembly with items."""
    svc = _get_service(db, current_user)
    assembly = svc.create_assembly(data)
    return AssemblyDetail.model_validate(assembly).model_dump()


@router.put("/assemblies/{assembly_id}", response_model=None)
async def update_assembly(
    assembly_id: int,
    data: AssemblyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an assembly."""
    svc = _get_service(db, current_user)
    assembly = svc.update_assembly(assembly_id, data)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    return AssemblyResponse.model_validate(assembly).model_dump()


@router.delete("/assemblies/{assembly_id}", status_code=204)
async def delete_assembly(
    assembly_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an assembly."""
    svc = _get_service(db, current_user)
    if not svc.delete_assembly(assembly_id):
        raise HTTPException(status_code=404, detail="Assembly not found")


# =============================================================================
# ASSEMBLY ITEMS
# =============================================================================

@router.post("/assembly-items", response_model=None, status_code=201)
async def create_assembly_item(
    data: AssemblyItemCreate,
    assembly_id: int = Query(..., description="Assembly to add item to"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add an item to an assembly."""
    svc = _get_service(db, current_user)
    try:
        item = svc.create_assembly_item(data, assembly_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AssemblyItemResponse.model_validate(item).model_dump()


@router.put("/assembly-items/{item_id}", response_model=None)
async def update_assembly_item(
    item_id: int,
    data: AssemblyItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an assembly item."""
    svc = _get_service(db, current_user)
    item = svc.update_assembly_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Assembly item not found")
    return AssemblyItemResponse.model_validate(item).model_dump()


@router.delete("/assembly-items/{item_id}", status_code=204)
async def delete_assembly_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an assembly item."""
    svc = _get_service(db, current_user)
    if not svc.delete_assembly_item(item_id):
        raise HTTPException(status_code=404, detail="Assembly item not found")
