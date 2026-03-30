"""API routes for Estimation"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_progress.schemas.progress import (
    EstimationItemCreate, EstimationItemUpdate, EstimationItemResponse,
)
from addons.agcm_progress.services.progress_service import ProgressService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProgressService:
    company_id = get_effective_company_id(current_user, db)
    return ProgressService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/estimation", response_model=None)
async def get_estimation_tree(
    project_id: int = Query(..., description="Filter by project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get hierarchical estimation tree with rollup totals."""
    svc = _get_service(db, current_user)
    tree = svc.get_estimation_tree(project_id)
    grand_total = sum(node.get("rollup_total", 0) for node in tree)
    return {"items": tree, "grand_total": grand_total}


@router.post("/estimation", response_model=None, status_code=201)
async def create_estimation_item(
    data: EstimationItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new estimation item."""
    svc = _get_service(db, current_user)
    item = svc.create_estimation_item(data)
    return EstimationItemResponse.model_validate(item).model_dump()


@router.put("/estimation/{item_id}", response_model=None)
async def update_estimation_item(
    item_id: int,
    data: EstimationItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an estimation item."""
    svc = _get_service(db, current_user)
    item = svc.update_estimation_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Estimation item not found")
    return EstimationItemResponse.model_validate(item).model_dump()


@router.delete("/estimation/{item_id}", status_code=204)
async def delete_estimation_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an estimation item and its children."""
    svc = _get_service(db, current_user)
    if not svc.delete_estimation_item(item_id):
        raise HTTPException(status_code=404, detail="Estimation item not found")
