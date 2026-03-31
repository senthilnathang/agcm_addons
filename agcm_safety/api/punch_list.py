"""API routes for Punch List"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_safety.schemas.punch_list import (
    PunchListItemCreate,
    PunchListItemUpdate,
    PunchListItemResponse,
)
from addons.agcm_safety.services.safety_service import SafetyService

router = APIRouter()


class AssignBody(BaseModel):
    assigned_to: int


def _get_service(db: Session, current_user) -> SafetyService:
    company_id = get_effective_company_id(current_user, db)
    return SafetyService(db, company_id, current_user.id)


@router.get("/punch-list")
async def list_punch_items(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List punch list items with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_punch_items(project_id, status, priority, search, page, page_size)
    result["items"] = [PunchListItemResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/punch-list/{item_id}", response_model=PunchListItemResponse)
async def get_punch_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a punch list item."""
    svc = _get_service(db, current_user)
    item = svc.get_punch_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    return item


@router.post("/punch-list", response_model=PunchListItemResponse, status_code=201)
async def create_punch_item(
    data: PunchListItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new punch list item."""
    svc = _get_service(db, current_user)
    item = svc.create_punch_item(data)
    return item


@router.put("/punch-list/{item_id}", response_model=PunchListItemResponse)
async def update_punch_item(
    item_id: int,
    data: PunchListItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a punch list item."""
    svc = _get_service(db, current_user)
    result = svc.update_punch_item(item_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    return result


@router.post("/punch-list/{item_id}/assign", response_model=PunchListItemResponse)
async def assign_punch_item(
    item_id: int,
    body: AssignBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Assign a punch list item to a user."""
    svc = _get_service(db, current_user)
    result = svc.assign_punch_item(item_id, body.assigned_to)
    if not result:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    return result


@router.post("/punch-list/{item_id}/complete", response_model=PunchListItemResponse)
async def complete_punch_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a punch list item as completed."""
    svc = _get_service(db, current_user)
    result = svc.complete_punch_item(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    return result


@router.post("/punch-list/{item_id}/verify", response_model=PunchListItemResponse)
async def verify_punch_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Verify a completed punch list item."""
    svc = _get_service(db, current_user)
    result = svc.verify_punch_item(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    return result


@router.delete("/punch-list/{item_id}", status_code=204)
async def delete_punch_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a punch list item."""
    svc = _get_service(db, current_user)
    if not svc.delete_punch_item(item_id):
        raise HTTPException(status_code=404, detail="Punch list item not found")
