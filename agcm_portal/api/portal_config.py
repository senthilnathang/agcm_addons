"""API routes for Portal Configuration"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_portal.schemas.portal_config import (
    PortalConfigCreate, PortalConfigUpdate, PortalConfigResponse,
)
from addons.agcm_portal.services.portal_service import PortalService

router = APIRouter()


def _get_service(db: Session, current_user) -> PortalService:
    company_id = get_effective_company_id(current_user, db)
    return PortalService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/portal-config/{project_id}", response_model=None)
async def get_portal_config(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get portal configuration for a project."""
    svc = _get_service(db, current_user)
    config = svc.get_portal_config(project_id)
    if not config:
        # Return defaults if no config exists yet
        return {
            "project_id": project_id,
            "client_portal_enabled": True,
            "sub_portal_enabled": True,
            "show_budget": False,
            "show_schedule": True,
            "show_documents": True,
            "show_photos": True,
            "show_daily_logs": False,
            "welcome_message": None,
        }
    return PortalConfigResponse.model_validate(config).model_dump()


@router.post("/portal-config", response_model=None, status_code=201)
async def create_or_update_portal_config(
    data: PortalConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create or update portal config for a project."""
    svc = _get_service(db, current_user)
    config = svc.create_or_update_portal_config(data)
    return PortalConfigResponse.model_validate(config).model_dump()


@router.put("/portal-config/{config_id}", response_model=None)
async def update_portal_config(
    config_id: int,
    data: PortalConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a portal config."""
    svc = _get_service(db, current_user)
    config = svc.update_portal_config(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="Portal config not found")
    return PortalConfigResponse.model_validate(config).model_dump()


@router.delete("/portal-config/{config_id}", status_code=204)
async def delete_portal_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a portal config."""
    svc = _get_service(db, current_user)
    if not svc.delete_portal_config(config_id):
        raise HTTPException(status_code=404, detail="Portal config not found")


@router.get("/dashboard/client/{project_id}", response_model=None)
async def client_dashboard(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get client dashboard data for a project."""
    svc = _get_service(db, current_user)
    return svc.get_client_dashboard(project_id)


@router.get("/dashboard/sub/{project_id}", response_model=None)
async def sub_dashboard(
    project_id: int,
    vendor_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get subcontractor dashboard data for a project."""
    svc = _get_service(db, current_user)
    return svc.get_sub_dashboard(project_id, vendor_name)
