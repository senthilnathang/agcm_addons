"""API routes for Tax Rates"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.schemas.finance import (
    TaxRateCreate, TaxRateUpdate, TaxRateResponse,
)
from addons.agcm_finance.services.finance_service import FinanceService

router = APIRouter()


def _get_service(db: Session, current_user) -> FinanceService:
    company_id = get_effective_company_id(current_user, db)
    return FinanceService(db, company_id, current_user.id)


@router.get("/tax-rates", response_model=list[TaxRateResponse])
async def list_tax_rates(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.list_tax_rates(active_only)


@router.post("/tax-rates", response_model=TaxRateResponse, status_code=201)
async def create_tax_rate(
    data: TaxRateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_tax_rate(data)


@router.put("/tax-rates/{rate_id}", response_model=TaxRateResponse)
async def update_tax_rate(
    rate_id: int,
    data: TaxRateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_tax_rate(rate_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return result


@router.delete("/tax-rates/{rate_id}", status_code=204)
async def delete_tax_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_tax_rate(rate_id):
        raise HTTPException(status_code=404, detail="Tax rate not found")
