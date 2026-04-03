"""API routes for Payment Applications (AIA G702/G703)"""

import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_procurement.models.payment_application import (
    PaymentApplication, PaymentApplicationLine,
)
from addons.agcm_procurement.models.subcontract import Subcontract, SubcontractSOVLine
from addons.agcm_procurement.schemas.payment_application import (
    PaymentApplicationCreate, PaymentApplicationUpdate,
    PaymentApplicationResponse, PaymentApplicationDetail,
    PaymentApplicationLineUpdate, PaymentApplicationLineResponse,
)

router = APIRouter()

SEQUENCE_PREFIX = "PA"
SEQUENCE_PADDING = 5


def _next_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(PaymentApplication.sequence_name)
        .filter(PaymentApplication.company_id == company_id, PaymentApplication.sequence_name.isnot(None))
        .order_by(PaymentApplication.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


@router.get("/payment-applications")
async def list_payment_applications(
    project_id: Optional[int] = None,
    subcontract_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    query = db.query(PaymentApplication).filter(PaymentApplication.company_id == company_id)
    if project_id:
        query = query.filter(PaymentApplication.project_id == project_id)
    if subcontract_id:
        query = query.filter(PaymentApplication.subcontract_id == subcontract_id)
    if status:
        query = query.filter(PaymentApplication.status == status)
    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(PaymentApplication.application_number.desc()).offset(skip).limit(page_size).all()
    return {
        "items": [PaymentApplicationResponse.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/payment-applications/{pa_id}")
async def get_payment_application(
    pa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pa = (
        db.query(PaymentApplication)
        .filter(PaymentApplication.id == pa_id, PaymentApplication.company_id == company_id)
        .first()
    )
    if not pa:
        raise HTTPException(status_code=404, detail="Payment application not found")
    return PaymentApplicationDetail.model_validate(pa).model_dump()


@router.post("/payment-applications", status_code=201)
async def create_payment_application(
    data: PaymentApplicationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)

    # Verify subcontract exists
    sc = (
        db.query(Subcontract)
        .filter(Subcontract.id == data.subcontract_id, Subcontract.company_id == company_id)
        .first()
    )
    if not sc:
        raise HTTPException(status_code=404, detail="Subcontract not found")

    pa = PaymentApplication(
        company_id=company_id,
        project_id=data.project_id,
        subcontract_id=data.subcontract_id,
        sequence_name=_next_sequence(db, company_id),
        application_number=data.application_number,
        period_from=data.period_from,
        period_to=data.period_to,
        notes=data.notes,
        scheduled_value=sc.revised_amount or sc.original_amount or 0,
        created_by=current_user.id,
    )
    db.add(pa)
    db.flush()

    # Auto-populate lines from SOV
    sov_lines = (
        db.query(SubcontractSOVLine)
        .filter(SubcontractSOVLine.subcontract_id == data.subcontract_id)
        .order_by(SubcontractSOVLine.display_order)
        .all()
    )

    for sov in sov_lines:
        line = PaymentApplicationLine(
            application_id=pa.id,
            company_id=company_id,
            sov_line_id=sov.id,
            description=sov.description,
            scheduled_value=sov.scheduled_value or 0,
            previous_billed=sov.billed_previous or 0,
            current_billed=0,
            stored_materials=0,
            total_completed=sov.billed_previous or 0,
            retainage=0,
            balance_to_finish=sov.scheduled_value - (sov.billed_previous or 0),
            pct_complete=sov.pct_complete or 0,
            display_order=sov.display_order or 0,
        )
        db.add(line)

    db.commit()
    db.refresh(pa)
    return PaymentApplicationDetail.model_validate(pa).model_dump()


@router.put("/payment-applications/{pa_id}")
async def update_payment_application(
    pa_id: int,
    data: PaymentApplicationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pa = (
        db.query(PaymentApplication)
        .filter(PaymentApplication.id == pa_id, PaymentApplication.company_id == company_id)
        .first()
    )
    if not pa:
        raise HTTPException(status_code=404, detail="Payment application not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pa, key, value)
    pa.updated_by = current_user.id
    db.commit()
    db.refresh(pa)
    return PaymentApplicationResponse.model_validate(pa).model_dump()


@router.post("/payment-applications/{pa_id}/certify")
async def certify_payment_application(
    pa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    pa = (
        db.query(PaymentApplication)
        .filter(PaymentApplication.id == pa_id, PaymentApplication.company_id == company_id)
        .first()
    )
    if not pa:
        raise HTTPException(status_code=404, detail="Payment application not found")

    pa.status = "certified"
    pa.certified_date = date.today()
    pa.certified_by = f"{current_user.username}" if hasattr(current_user, "username") else str(current_user.id)
    pa.updated_by = current_user.id

    # Recalculate totals from lines
    lines = (
        db.query(PaymentApplicationLine)
        .filter(PaymentApplicationLine.application_id == pa_id)
        .all()
    )
    pa.current_billed = sum(l.current_billed for l in lines)
    pa.stored_materials = sum(l.stored_materials for l in lines)
    pa.total_completed = pa.previous_billed + pa.current_billed + pa.stored_materials
    if pa.scheduled_value:
        pa.pct_complete = (pa.total_completed / pa.scheduled_value) * 100
    pa.net_payment_due = pa.current_billed + pa.stored_materials - pa.retainage_held + pa.retainage_released

    db.commit()
    db.refresh(pa)
    return PaymentApplicationResponse.model_validate(pa).model_dump()


@router.post("/payment-application-lines/{line_id}")
async def update_payment_application_line(
    line_id: int,
    data: PaymentApplicationLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    line = (
        db.query(PaymentApplicationLine)
        .filter(PaymentApplicationLine.id == line_id, PaymentApplicationLine.company_id == company_id)
        .first()
    )
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(line, key, value)

    # Recalculate line totals
    line.total_completed = (line.previous_billed or 0) + (line.current_billed or 0) + (line.stored_materials or 0)
    line.balance_to_finish = (line.scheduled_value or 0) - line.total_completed
    if line.scheduled_value:
        line.pct_complete = (line.total_completed / line.scheduled_value) * 100

    db.commit()
    db.refresh(line)
    return PaymentApplicationLineResponse.model_validate(line).model_dump()


@router.get("/payment-applications/{pa_id}/g702-summary")
async def get_g702_summary(
    pa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    AIA G702 Application and Certificate for Payment summary.

    Returns header info + computed totals matching AIA G702 form fields.
    """
    company_id = get_effective_company_id(current_user, db)
    pa = (
        db.query(PaymentApplication)
        .filter(PaymentApplication.id == pa_id, PaymentApplication.company_id == company_id)
        .first()
    )
    if not pa:
        raise HTTPException(status_code=404, detail="Payment application not found")

    # Load subcontract for contractor info
    sc = db.query(Subcontract).filter(Subcontract.id == pa.subcontract_id).first()

    # Load project for header
    try:
        from addons.agcm.models.project import Project
        project = db.query(Project).filter(Project.id == pa.project_id).first()
        project_name = project.name if project else ""
        project_address = getattr(project, "address", "") or ""
    except ImportError:
        project_name = ""
        project_address = ""

    # G702 computed fields
    original_contract_sum = sc.original_amount if sc else pa.scheduled_value
    net_change_by_cos = pa.change_order_total or 0
    current_contract_sum = original_contract_sum + net_change_by_cos
    total_completed_stored = pa.total_completed or 0
    retainage_pct = pa.retainage_pct or 10.0
    retainage_amount = round(total_completed_stored * retainage_pct / 100, 2)
    total_earned_less_retainage = round(total_completed_stored - retainage_amount, 2)
    less_previous_certificates = pa.previous_billed or 0
    current_payment_due = round(total_earned_less_retainage - less_previous_certificates, 2)
    balance_to_finish = round(current_contract_sum - total_completed_stored, 2)

    # G703 continuation sheet (line items)
    g703_lines = []
    for line in (pa.lines or []):
        g703_lines.append({
            "item_number": getattr(line, "item_number", None) or str(line.display_order + 1),
            "description": line.description,
            "scheduled_value": line.scheduled_value or 0,
            "from_previous_work": line.previous_billed or 0,
            "from_previous_materials": getattr(line, "previous_stored_materials", 0) or 0,
            "this_period_work": line.current_billed or 0,
            "this_period_materials": line.stored_materials or 0,
            "total_completed_stored": line.total_completed or 0,
            "pct_complete": round(line.pct_complete or 0, 1),
            "balance_to_finish": line.balance_to_finish or 0,
            "retainage": line.retainage or 0,
        })

    return {
        # G702 Header
        "application_number": pa.application_number,
        "period_from": pa.period_from.isoformat() if pa.period_from else None,
        "period_to": pa.period_to.isoformat() if pa.period_to else None,
        "project_name": project_name,
        "project_address": project_address,
        "contractor_name": sc.vendor_name if sc else "",
        "contract_date": pa.contract_date.isoformat() if pa.contract_date else None,
        # G702 Amounts
        "original_contract_sum": round(original_contract_sum, 2),
        "net_change_by_change_orders": round(net_change_by_cos, 2),
        "current_contract_sum": round(current_contract_sum, 2),
        "total_completed_and_stored": round(total_completed_stored, 2),
        "retainage_pct": retainage_pct,
        "retainage_amount": retainage_amount,
        "total_earned_less_retainage": total_earned_less_retainage,
        "less_previous_certificates": round(less_previous_certificates, 2),
        "current_payment_due": current_payment_due,
        "balance_to_finish": balance_to_finish,
        "pct_complete": round(pa.pct_complete or 0, 1),
        # Certification
        "status": pa.status,
        "certified_by": pa.certified_by,
        "certified_date": pa.certified_date.isoformat() if pa.certified_date else None,
        # G703 Continuation Sheet
        "g703_lines": g703_lines,
    }
