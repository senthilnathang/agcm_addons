"""API routes for Expenses"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseDetail,
    ExpenseLineCreate,
    ExpenseLineUpdate,
    ExpenseLineResponse,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/expenses")
async def list_expenses(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List expenses with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_expenses(project_id, status, page, page_size)
    result["items"] = [ExpenseResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/expenses/{expense_id}", response_model=ExpenseDetail)
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get expense details with line items."""
    svc = _get_service(db, current_user)
    detail = svc.get_expense_detail(expense_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Expense not found")
    return detail


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new expense."""
    svc = _get_service(db, current_user)
    return svc.create_expense(data)


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an expense."""
    svc = _get_service(db, current_user)
    result = svc.update_expense(expense_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Expense not found")
    return result


@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an expense."""
    svc = _get_service(db, current_user)
    if not svc.delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve an expense and post cost to budget."""
    svc = _get_service(db, current_user)
    result = svc.approve_expense(expense_id)
    if not result:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ExpenseResponse.model_validate(result).model_dump()


# --- Expense Line Endpoints ---

@router.post("/expense-lines", response_model=ExpenseLineResponse, status_code=201)
async def create_expense_line(
    data: ExpenseLineCreate,
    expense_id: int = Query(..., description="Parent expense ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a line item to an expense."""
    svc = _get_service(db, current_user)
    result = svc.add_expense_line(data, expense_id)
    if not result:
        raise HTTPException(status_code=404, detail="Expense not found")
    return result


@router.put("/expense-lines/{line_id}", response_model=ExpenseLineResponse)
async def update_expense_line(
    line_id: int,
    data: ExpenseLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an expense line item."""
    svc = _get_service(db, current_user)
    result = svc.update_expense_line(line_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Line item not found")
    return result


@router.delete("/expense-lines/{line_id}", status_code=204)
async def delete_expense_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an expense line item."""
    svc = _get_service(db, current_user)
    if not svc.delete_expense_line(line_id):
        raise HTTPException(status_code=404, detail="Line item not found")
