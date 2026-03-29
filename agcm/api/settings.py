"""API routes for AGCM Settings / Lookup Tables"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm.models.lookups import AccidentType, InspectionType, Trade, ViolationType

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LookupCreate(BaseModel):
    name: str


class LookupUpdate(BaseModel):
    name: str


class LookupResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _list(model, db: Session, company_id: int):
    return db.query(model).filter(model.company_id == company_id).order_by(model.name).all()


def _create(model, db: Session, company_id: int, data: LookupCreate):
    obj = model(name=data.name, company_id=company_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _update(model, db: Session, company_id: int, obj_id: int, data: LookupUpdate):
    obj = db.query(model).filter(model.id == obj_id, model.company_id == company_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    obj.name = data.name
    db.commit()
    db.refresh(obj)
    return obj


def _delete(model, db: Session, company_id: int, obj_id: int):
    obj = db.query(model).filter(model.id == obj_id, model.company_id == company_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------

@router.get("/trades", response_model=list[LookupResponse])
async def list_trades(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _list(Trade, db, company_id)


@router.post("/trades", response_model=LookupResponse, status_code=201)
async def create_trade(
    data: LookupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _create(Trade, db, company_id, data)


@router.put("/trades/{trade_id}", response_model=LookupResponse)
async def update_trade(
    trade_id: int,
    data: LookupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _update(Trade, db, company_id, trade_id, data)


@router.delete("/trades/{trade_id}", status_code=204)
async def delete_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    _delete(Trade, db, company_id, trade_id)


# ---------------------------------------------------------------------------
# Inspection Types
# ---------------------------------------------------------------------------

@router.get("/inspection-types", response_model=list[LookupResponse])
async def list_inspection_types(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _list(InspectionType, db, company_id)


@router.post("/inspection-types", response_model=LookupResponse, status_code=201)
async def create_inspection_type(
    data: LookupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _create(InspectionType, db, company_id, data)


@router.put("/inspection-types/{type_id}", response_model=LookupResponse)
async def update_inspection_type(
    type_id: int,
    data: LookupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _update(InspectionType, db, company_id, type_id, data)


@router.delete("/inspection-types/{type_id}", status_code=204)
async def delete_inspection_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    _delete(InspectionType, db, company_id, type_id)


# ---------------------------------------------------------------------------
# Accident Types
# ---------------------------------------------------------------------------

@router.get("/accident-types", response_model=list[LookupResponse])
async def list_accident_types(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _list(AccidentType, db, company_id)


@router.post("/accident-types", response_model=LookupResponse, status_code=201)
async def create_accident_type(
    data: LookupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _create(AccidentType, db, company_id, data)


@router.put("/accident-types/{type_id}", response_model=LookupResponse)
async def update_accident_type(
    type_id: int,
    data: LookupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _update(AccidentType, db, company_id, type_id, data)


@router.delete("/accident-types/{type_id}", status_code=204)
async def delete_accident_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    _delete(AccidentType, db, company_id, type_id)


# ---------------------------------------------------------------------------
# Violation Types
# ---------------------------------------------------------------------------

@router.get("/violation-types", response_model=list[LookupResponse])
async def list_violation_types(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _list(ViolationType, db, company_id)


@router.post("/violation-types", response_model=LookupResponse, status_code=201)
async def create_violation_type(
    data: LookupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _create(ViolationType, db, company_id, data)


@router.put("/violation-types/{type_id}", response_model=LookupResponse)
async def update_violation_type(
    type_id: int,
    data: LookupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    return _update(ViolationType, db, company_id, type_id, data)


@router.delete("/violation-types/{type_id}", status_code=204)
async def delete_violation_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    _delete(ViolationType, db, company_id, type_id)
