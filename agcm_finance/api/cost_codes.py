"""API routes for Cost Codes"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    CostCodeCreate,
    CostCodeUpdate,
    CostCodeResponse,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/cost-codes")
async def list_cost_codes(
    project_id: int = Query(..., description="Project ID"),
    tree: bool = Query(False, description="Return as tree structure"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List cost codes for a project, optionally as a tree."""
    svc = _get_service(db, current_user)
    if tree:
        return svc.get_cost_code_tree(project_id)
    codes = svc.list_cost_codes(project_id)
    return [CostCodeResponse.model_validate(c).model_dump() for c in codes]


@router.post("/cost-codes", response_model=CostCodeResponse, status_code=201)
async def create_cost_code(
    data: CostCodeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new cost code."""
    svc = _get_service(db, current_user)
    return svc.create_cost_code(data)


@router.put("/cost-codes/{cc_id}", response_model=CostCodeResponse)
async def update_cost_code(
    cc_id: int,
    data: CostCodeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a cost code."""
    svc = _get_service(db, current_user)
    result = svc.update_cost_code(cc_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Cost code not found")
    return result


@router.delete("/cost-codes/{cc_id}", status_code=204)
async def delete_cost_code(
    cc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a cost code."""
    svc = _get_service(db, current_user)
    if not svc.delete_cost_code(cc_id):
        raise HTTPException(status_code=404, detail="Cost code not found")
