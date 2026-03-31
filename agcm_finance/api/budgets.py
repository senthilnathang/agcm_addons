"""API routes for Budgets"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetSummary,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/budgets")
async def list_budgets(
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List budget lines for a project."""
    svc = _get_service(db, current_user)
    budgets = svc.list_budgets(project_id)
    return [BudgetResponse.model_validate(b).model_dump() for b in budgets]


@router.get("/budget/summary")
async def get_budget_summary(
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get aggregated budget summary for a project."""
    svc = _get_service(db, current_user)
    summary = svc.get_budget_summary(project_id)
    summary["lines"] = [BudgetResponse.model_validate(b).model_dump() for b in summary["lines"]]
    return summary


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new budget line."""
    svc = _get_service(db, current_user)
    return svc.create_budget(data)


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a budget line."""
    svc = _get_service(db, current_user)
    result = svc.update_budget(budget_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")
    return result


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a budget line."""
    svc = _get_service(db, current_user)
    if not svc.delete_budget(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")


@router.get("/budget/forecast")
async def get_budget_forecast(
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get EAC/ETC budget forecast for a project."""
    svc = _get_service(db, current_user)
    return svc.get_budget_forecast(project_id)
