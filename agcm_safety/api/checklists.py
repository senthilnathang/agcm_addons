"""API routes for Checklist Templates"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_safety.schemas.checklist import (
    ChecklistTemplateCreate,
    ChecklistTemplateUpdate,
    ChecklistTemplateResponse,
    ChecklistTemplateDetail,
)
from addons.agcm_safety.services.safety_service import SafetyService

router = APIRouter()


def _get_service(db: Session, current_user) -> SafetyService:
    company_id = get_effective_company_id(current_user, db)
    return SafetyService(db, company_id, current_user.id)


@router.get("/checklists")
async def list_templates(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List checklist templates with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_templates(category, is_active, search, page, page_size)
    result["items"] = [ChecklistTemplateResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/checklists/{template_id}", response_model=ChecklistTemplateDetail)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get checklist template with items."""
    svc = _get_service(db, current_user)
    detail = svc.get_template_detail(template_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Checklist template not found")
    return detail


@router.post("/checklists", response_model=ChecklistTemplateResponse, status_code=201)
async def create_template(
    data: ChecklistTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new checklist template."""
    svc = _get_service(db, current_user)
    tpl = svc.create_template(data)
    return tpl


@router.put("/checklists/{template_id}", response_model=ChecklistTemplateResponse)
async def update_template(
    template_id: int,
    data: ChecklistTemplateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a checklist template."""
    svc = _get_service(db, current_user)
    result = svc.update_template(template_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist template not found")
    return result


@router.delete("/checklists/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a checklist template."""
    svc = _get_service(db, current_user)
    if not svc.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Checklist template not found")
