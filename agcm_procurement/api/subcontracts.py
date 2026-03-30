"""API routes for Subcontracts."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_procurement.schemas.procurement import (
    SubcontractCreate, SubcontractUpdate, SubcontractResponse, SubcontractDetail,
    SubcontractSOVLineCreate, SubcontractSOVLineUpdate, SubcontractSOVLineResponse,
    ComplianceDocCreate, ComplianceDocUpdate, ComplianceDocResponse,
    UpdateBillingRequest,
)
from addons.agcm_procurement.services.procurement_service import ProcurementService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProcurementService:
    company_id = get_effective_company_id(current_user, db)
    return ProcurementService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/subcontracts", response_model=None)
async def list_subcontracts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List subcontracts with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_subcontracts(
        page=page, page_size=page_size,
        project_id=project_id, status=status, search=search,
    )


@router.get("/subcontracts/{sc_id}", response_model=None)
async def get_subcontract(
    sc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get subcontract detail with SOV lines and compliance docs."""
    svc = _get_service(db, current_user)
    detail = svc.get_subcontract_detail(sc_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return detail


@router.post("/subcontracts", response_model=None, status_code=201)
async def create_subcontract(
    data: SubcontractCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new subcontract with optional SOV lines."""
    svc = _get_service(db, current_user)
    sc = svc.create_subcontract(data)
    return SubcontractResponse.model_validate(sc).model_dump()


@router.put("/subcontracts/{sc_id}", response_model=None)
async def update_subcontract(
    sc_id: int,
    data: SubcontractUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a subcontract."""
    svc = _get_service(db, current_user)
    sc = svc.update_subcontract(sc_id, data)
    if not sc:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return SubcontractResponse.model_validate(sc).model_dump()


@router.delete("/subcontracts/{sc_id}", status_code=204)
async def delete_subcontract(
    sc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a subcontract."""
    svc = _get_service(db, current_user)
    if not svc.delete_subcontract(sc_id):
        raise HTTPException(status_code=404, detail="Subcontract not found")


@router.post("/subcontracts/{sc_id}/approve", response_model=None)
async def approve_subcontract(
    sc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a subcontract."""
    svc = _get_service(db, current_user)
    sc = svc.approve_subcontract(sc_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return SubcontractResponse.model_validate(sc).model_dump()


@router.post("/subcontracts/{sc_id}/update-billing", response_model=None)
async def update_billing(
    sc_id: int,
    data: UpdateBillingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update billed_current on SOV lines and recalculate subcontract totals."""
    svc = _get_service(db, current_user)
    sc = svc.update_sov_billing(sc_id, data.sov_updates)
    if not sc:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return SubcontractResponse.model_validate(sc).model_dump()


# ---- SOV Lines ----

@router.post("/sov-lines", response_model=None, status_code=201)
async def create_sov_line(
    data: SubcontractSOVLineCreate,
    subcontract_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add an SOV line to a subcontract."""
    svc = _get_service(db, current_user)
    sov = svc.create_sov_line(data, subcontract_id)
    if not sov:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return SubcontractSOVLineResponse.model_validate(sov).model_dump()


@router.put("/sov-lines/{line_id}", response_model=None)
async def update_sov_line(
    line_id: int,
    data: SubcontractSOVLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an SOV line."""
    svc = _get_service(db, current_user)
    sov = svc.update_sov_line(line_id, data)
    if not sov:
        raise HTTPException(status_code=404, detail="SOV line not found")
    return SubcontractSOVLineResponse.model_validate(sov).model_dump()


@router.delete("/sov-lines/{line_id}", status_code=204)
async def delete_sov_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an SOV line."""
    svc = _get_service(db, current_user)
    if not svc.delete_sov_line(line_id):
        raise HTTPException(status_code=404, detail="SOV line not found")


# ---- Compliance Docs ----

@router.post("/compliance-docs", response_model=None, status_code=201)
async def create_compliance_doc(
    data: ComplianceDocCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a compliance document to a subcontract."""
    svc = _get_service(db, current_user)
    doc = svc.create_compliance_doc(data)
    if not doc:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return ComplianceDocResponse.model_validate(doc).model_dump()


@router.put("/compliance-docs/{doc_id}", response_model=None)
async def update_compliance_doc(
    doc_id: int,
    data: ComplianceDocUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a compliance document."""
    svc = _get_service(db, current_user)
    doc = svc.update_compliance_doc(doc_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Compliance document not found")
    return ComplianceDocResponse.model_validate(doc).model_dump()


@router.delete("/compliance-docs/{doc_id}", status_code=204)
async def delete_compliance_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a compliance document."""
    svc = _get_service(db, current_user)
    if not svc.delete_compliance_doc(doc_id):
        raise HTTPException(status_code=404, detail="Compliance document not found")
