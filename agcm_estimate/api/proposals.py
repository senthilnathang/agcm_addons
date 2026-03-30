"""API routes for Proposals."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_estimate.schemas.estimate import (
    ProposalCreate, ProposalUpdate, ProposalResponse,
)
from addons.agcm_estimate.services.estimate_service import EstimateService

router = APIRouter()


def _get_service(db: Session, current_user) -> EstimateService:
    company_id = get_effective_company_id(current_user, db)
    return EstimateService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/proposals", response_model=None)
async def list_proposals(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """List proposals with optional filters."""
    svc = _get_service(db, current_user)
    return svc.list_proposals(
        project_id=project_id, status=status, page=page, page_size=page_size,
    )


@router.get("/proposals/{proposal_id}", response_model=None)
async def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get proposal detail."""
    svc = _get_service(db, current_user)
    proposal = svc.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.post("/proposals", response_model=None, status_code=201)
async def create_proposal(
    data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a proposal from an estimate."""
    svc = _get_service(db, current_user)
    proposal = svc.generate_proposal(data.estimate_id, data)
    if not proposal:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.put("/proposals/{proposal_id}", response_model=None)
async def update_proposal(
    proposal_id: int,
    data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a proposal."""
    svc = _get_service(db, current_user)
    proposal = svc.update_proposal(proposal_id, data)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.delete("/proposals/{proposal_id}", status_code=204)
async def delete_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a proposal."""
    svc = _get_service(db, current_user)
    if not svc.delete_proposal(proposal_id):
        raise HTTPException(status_code=404, detail="Proposal not found")


@router.post("/proposals/{proposal_id}/send", response_model=None)
async def send_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a proposal as sent."""
    svc = _get_service(db, current_user)
    proposal = svc.send_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.post("/proposals/{proposal_id}/approve", response_model=None)
async def approve_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a proposal."""
    svc = _get_service(db, current_user)
    proposal = svc.approve_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.post("/proposals/{proposal_id}/reject", response_model=None)
async def reject_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject a proposal."""
    svc = _get_service(db, current_user)
    proposal = svc.reject_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal).model_dump()


@router.get("/proposals/{proposal_id}/pdf", response_model=None)
async def get_proposal_pdf(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a PDF for the proposal (returns HTML for now)."""
    svc = _get_service(db, current_user)
    proposal = svc.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Get estimate detail for the proposal
    est_detail = svc.get_estimate_detail(proposal.estimate_id)

    html = f"""<!DOCTYPE html>
<html>
<head><title>Proposal {proposal.sequence_name}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; }}
h1 {{ color: #1a1a1a; }}
.section {{ margin: 20px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #f5f5f5; }}
.total-row {{ font-weight: bold; background-color: #fafafa; }}
</style></head>
<body>
<h1>Proposal: {proposal.name}</h1>
<p><strong>Ref:</strong> {proposal.sequence_name}</p>
<p><strong>Client:</strong> {proposal.client_name}</p>
<p><strong>Valid Until:</strong> {proposal.valid_until or 'N/A'}</p>

<div class="section">
<h2>Scope of Work</h2>
<p>{proposal.scope_of_work or 'N/A'}</p>
</div>

<div class="section">
<h2>Estimate Summary</h2>
<table>
<tr><th>Description</th><th>Amount</th></tr>
<tr><td>Subtotal</td><td>${est_detail['summary']['subtotal']:,.2f}</td></tr>
<tr><td>Markup</td><td>${est_detail['summary']['markup_total']:,.2f}</td></tr>
<tr><td>Tax</td><td>${est_detail['summary']['tax_total']:,.2f}</td></tr>
<tr class="total-row"><td>Grand Total</td><td>${est_detail['summary']['grand_total']:,.2f}</td></tr>
</table>
</div>

<div class="section">
<h2>Terms & Conditions</h2>
<p>{proposal.terms_and_conditions or 'N/A'}</p>
</div>

<div class="section">
<h2>Exclusions</h2>
<p>{proposal.exclusions or 'N/A'}</p>
</div>

<div class="section">
<h2>Payment Schedule</h2>
<p>{proposal.payment_schedule or 'N/A'}</p>
</div>
</body></html>"""

    return HTMLResponse(content=html)
