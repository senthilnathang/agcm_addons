"""API routes for Prime Contract Management"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_finance.models.prime_contract import PrimeContract
from addons.agcm_finance.schemas.prime_contract import (
    PrimeContractCreate, PrimeContractUpdate, PrimeContractResponse,
)

router = APIRouter()

SEQUENCE_PREFIX = "PC"
SEQUENCE_PADDING = 5


def _next_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(PrimeContract.sequence_name)
        .filter(PrimeContract.company_id == company_id, PrimeContract.sequence_name.isnot(None))
        .order_by(PrimeContract.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


@router.get("/prime-contracts")
async def list_prime_contracts(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    query = db.query(PrimeContract).filter(PrimeContract.company_id == company_id)
    if project_id:
        query = query.filter(PrimeContract.project_id == project_id)
    if status:
        query = query.filter(PrimeContract.status == status)
    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(PrimeContract.id.desc()).offset(skip).limit(page_size).all()
    return {
        "items": [PrimeContractResponse.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/prime-contracts/{pc_id}")
async def get_prime_contract(
    pc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pc = (
        db.query(PrimeContract)
        .filter(PrimeContract.id == pc_id, PrimeContract.company_id == company_id)
        .first()
    )
    if not pc:
        raise HTTPException(status_code=404, detail="Prime contract not found")
    return PrimeContractResponse.model_validate(pc).model_dump()


@router.post("/prime-contracts", status_code=201)
async def create_prime_contract(
    data: PrimeContractCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    revised = (data.original_value or 0) + (data.approved_changes or 0)
    pc = PrimeContract(
        company_id=company_id,
        project_id=data.project_id,
        sequence_name=_next_sequence(db, company_id),
        contract_number=data.contract_number,
        title=data.title,
        description=data.description,
        owner_name=data.owner_name,
        status=data.status,
        original_value=data.original_value,
        approved_changes=data.approved_changes,
        revised_value=revised,
        retainage_pct=data.retainage_pct,
        start_date=data.start_date,
        end_date=data.end_date,
        executed_date=data.executed_date,
        contract_type=data.contract_type,
        payment_terms=data.payment_terms,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return PrimeContractResponse.model_validate(pc).model_dump()


@router.put("/prime-contracts/{pc_id}")
async def update_prime_contract(
    pc_id: int,
    data: PrimeContractUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pc = (
        db.query(PrimeContract)
        .filter(PrimeContract.id == pc_id, PrimeContract.company_id == company_id)
        .first()
    )
    if not pc:
        raise HTTPException(status_code=404, detail="Prime contract not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pc, key, value)
    # Recalculate revised_value
    pc.revised_value = (pc.original_value or 0) + (pc.approved_changes or 0)
    pc.updated_by = current_user.id
    db.commit()
    db.refresh(pc)
    return PrimeContractResponse.model_validate(pc).model_dump()


@router.delete("/prime-contracts/{pc_id}", status_code=204)
async def delete_prime_contract(
    pc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pc = (
        db.query(PrimeContract)
        .filter(PrimeContract.id == pc_id, PrimeContract.company_id == company_id)
        .first()
    )
    if not pc:
        raise HTTPException(status_code=404, detail="Prime contract not found")
    db.delete(pc)
    db.commit()
