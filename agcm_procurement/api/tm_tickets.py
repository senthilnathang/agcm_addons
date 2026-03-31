"""API routes for T&M Tickets (Time and Material)"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_procurement.models.tm_ticket import TMTicket, TMTicketLine
from addons.agcm_procurement.schemas.tm_ticket import (
    TMTicketCreate, TMTicketUpdate,
    TMTicketResponse, TMTicketDetail,
    TMTicketLineCreate, TMTicketLineResponse,
)

router = APIRouter()

SEQUENCE_PREFIX = "TM"
SEQUENCE_PADDING = 5


def _next_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(TMTicket.sequence_name)
        .filter(TMTicket.company_id == company_id, TMTicket.sequence_name.isnot(None))
        .order_by(TMTicket.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


def _recalc_totals(ticket, lines):
    """Recalculate ticket totals from lines."""
    ticket.labor_total = sum(l.total_cost for l in lines if l.line_type == "labor")
    ticket.material_total = sum(l.total_cost for l in lines if l.line_type == "material")
    ticket.equipment_total = sum(l.total_cost for l in lines if l.line_type == "equipment")
    subtotal = ticket.labor_total + ticket.material_total + ticket.equipment_total
    ticket.markup_amount = subtotal * (ticket.markup_pct or 0) / 100
    ticket.total_amount = subtotal + ticket.markup_amount


@router.get("/tm-tickets")
async def list_tm_tickets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    query = db.query(TMTicket).filter(TMTicket.company_id == company_id)
    if project_id:
        query = query.filter(TMTicket.project_id == project_id)
    if status:
        query = query.filter(TMTicket.status == status)
    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(TMTicket.id.desc()).offset(skip).limit(page_size).all()
    return {
        "items": [TMTicketResponse.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/tm-tickets/{ticket_id}")
async def get_tm_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = (
        db.query(TMTicket)
        .filter(TMTicket.id == ticket_id, TMTicket.company_id == company_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="T&M ticket not found")
    return TMTicketDetail.model_validate(ticket).model_dump()


@router.post("/tm-tickets", status_code=201)
async def create_tm_ticket(
    data: TMTicketCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = TMTicket(
        company_id=company_id,
        project_id=data.project_id,
        sequence_name=_next_sequence(db, company_id),
        ticket_number=data.ticket_number,
        date=data.date,
        description=data.description,
        vendor_name=data.vendor_name,
        change_order_id=data.change_order_id,
        markup_pct=data.markup_pct,
        notes=data.notes,
        submitted_by=current_user.id,
        created_by=current_user.id,
    )
    db.add(ticket)
    db.flush()

    lines = []
    if data.lines:
        for i, line_data in enumerate(data.lines):
            line = TMTicketLine(
                ticket_id=ticket.id,
                company_id=company_id,
                line_type=line_data.line_type,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_cost=line_data.unit_cost,
                total_cost=line_data.total_cost or (line_data.quantity * line_data.unit_cost),
                display_order=line_data.display_order or i,
            )
            db.add(line)
            lines.append(line)

    _recalc_totals(ticket, lines)
    db.commit()
    db.refresh(ticket)
    return TMTicketDetail.model_validate(ticket).model_dump()


@router.put("/tm-tickets/{ticket_id}")
async def update_tm_ticket(
    ticket_id: int,
    data: TMTicketUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = (
        db.query(TMTicket)
        .filter(TMTicket.id == ticket_id, TMTicket.company_id == company_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="T&M ticket not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    ticket.updated_by = current_user.id

    # Recalculate if markup changed
    if "markup_pct" in update_data:
        lines = db.query(TMTicketLine).filter(TMTicketLine.ticket_id == ticket_id).all()
        _recalc_totals(ticket, lines)

    db.commit()
    db.refresh(ticket)
    return TMTicketResponse.model_validate(ticket).model_dump()


@router.delete("/tm-tickets/{ticket_id}", status_code=204)
async def delete_tm_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = (
        db.query(TMTicket)
        .filter(TMTicket.id == ticket_id, TMTicket.company_id == company_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="T&M ticket not found")
    db.delete(ticket)
    db.commit()


@router.post("/tm-tickets/{ticket_id}/approve")
async def approve_tm_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = (
        db.query(TMTicket)
        .filter(TMTicket.id == ticket_id, TMTicket.company_id == company_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="T&M ticket not found")

    ticket.status = "approved"
    ticket.approved_by = current_user.id
    ticket.updated_by = current_user.id
    db.commit()
    db.refresh(ticket)
    return TMTicketResponse.model_validate(ticket).model_dump()


@router.post("/tm-ticket-lines", status_code=201)
async def add_tm_ticket_line(
    data: TMTicketLineCreate,
    ticket_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = get_effective_company_id(current_user, db)
    ticket = (
        db.query(TMTicket)
        .filter(TMTicket.id == ticket_id, TMTicket.company_id == company_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="T&M ticket not found")

    line = TMTicketLine(
        ticket_id=ticket_id,
        company_id=company_id,
        line_type=data.line_type,
        description=data.description,
        quantity=data.quantity,
        unit=data.unit,
        unit_cost=data.unit_cost,
        total_cost=data.total_cost or (data.quantity * data.unit_cost),
        display_order=data.display_order,
    )
    db.add(line)
    db.flush()

    # Recalculate ticket totals
    all_lines = db.query(TMTicketLine).filter(TMTicketLine.ticket_id == ticket_id).all()
    _recalc_totals(ticket, all_lines)

    db.commit()
    db.refresh(line)
    return TMTicketLineResponse.model_validate(line).model_dump()
