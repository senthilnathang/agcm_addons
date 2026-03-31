"""API routes for Selections"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_portal.schemas.selection import (
    SelectionCreate, SelectionUpdate, SelectionResponse,
    SelectionOptionCreate, SelectionOptionUpdate, SelectionOptionResponse,
)
from addons.agcm_portal.services.portal_service import PortalService

router = APIRouter()


def _get_service(db: Session, current_user) -> PortalService:
    company_id = get_effective_company_id(current_user, db)
    return PortalService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/selections", response_model=None)
async def list_selections(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List selections with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_selections(
        page=page, page_size=page_size,
        project_id=project_id, status=status,
        category=category, search=search,
    )


@router.get("/selections/{selection_id}", response_model=None)
async def get_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get selection details with options."""
    svc = _get_service(db, current_user)
    selection = svc.get_selection(selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return SelectionResponse.model_validate(selection).model_dump()


@router.post("/selections", response_model=None, status_code=201)
async def create_selection(
    data: SelectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new selection."""
    svc = _get_service(db, current_user)
    selection = svc.create_selection(data)
    return SelectionResponse.model_validate(selection).model_dump()


@router.put("/selections/{selection_id}", response_model=None)
async def update_selection(
    selection_id: int,
    data: SelectionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a selection."""
    svc = _get_service(db, current_user)
    selection = svc.update_selection(selection_id, data)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return SelectionResponse.model_validate(selection).model_dump()


@router.delete("/selections/{selection_id}", status_code=204)
async def delete_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a selection."""
    svc = _get_service(db, current_user)
    if not svc.delete_selection(selection_id):
        raise HTTPException(status_code=404, detail="Selection not found")


@router.post("/selections/{selection_id}/approve", response_model=None)
async def approve_selection(
    selection_id: int,
    option_id: int = Query(..., description="ID of the chosen option"),
    decided_by: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a selection by choosing an option."""
    svc = _get_service(db, current_user)
    selection = svc.approve_selection(selection_id, option_id, decided_by)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection or option not found")
    return SelectionResponse.model_validate(selection).model_dump()


@router.post("/selections/{selection_id}/reject", response_model=None)
async def reject_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject a selection."""
    svc = _get_service(db, current_user)
    selection = svc.reject_selection(selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return SelectionResponse.model_validate(selection).model_dump()


# --- Selection Options ---

@router.post("/selections/{selection_id}/options", response_model=None, status_code=201)
async def create_option(
    selection_id: int,
    data: SelectionOptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add an option to a selection."""
    svc = _get_service(db, current_user)
    option = svc.create_option(selection_id, data)
    if not option:
        raise HTTPException(status_code=404, detail="Selection not found")
    return SelectionOptionResponse.model_validate(option).model_dump()


@router.put("/options/{option_id}", response_model=None)
async def update_option(
    option_id: int,
    data: SelectionOptionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a selection option."""
    svc = _get_service(db, current_user)
    option = svc.update_option(option_id, data)
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")
    return SelectionOptionResponse.model_validate(option).model_dump()


@router.delete("/options/{option_id}", status_code=204)
async def delete_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a selection option."""
    svc = _get_service(db, current_user)
    if not svc.delete_option(option_id):
        raise HTTPException(status_code=404, detail="Option not found")
