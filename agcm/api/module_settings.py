"""API routes for AGCM module settings."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user, get_effective_company_id

router = APIRouter()


class SettingsUpdateRequest(BaseModel):
    default_retention_pct: Optional[float] = Field(None, ge=0, le=100)
    default_markup_pct: Optional[float] = Field(None, ge=0, le=1000)
    default_tax_rate_pct: Optional[float] = Field(None, ge=0, le=100)
    default_payment_terms: Optional[str] = None
    po_number_prefix: Optional[str] = None
    invoice_number_prefix: Optional[str] = None
    currency_code: Optional[str] = None
    working_hours_per_day: Optional[float] = Field(None, ge=1, le=24)
    overtime_multiplier: Optional[float] = Field(None, ge=1, le=5)
    settings_json: Optional[dict] = None
    notes: Optional[str] = None


def _get_service(db, current_user):
    from addons.agcm.services.settings_service import SettingsService
    company_id = get_effective_company_id(current_user, db)
    return SettingsService(db, company_id, current_user.id)


@router.get("/settings/modules")
async def list_all_module_settings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List settings for all AGCM modules (configured + defaults)."""
    svc = _get_service(db, current_user)
    return svc.list_all_modules()


@router.get("/settings/modules/{module_name}")
async def get_module_settings(
    module_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get settings for a specific module."""
    svc = _get_service(db, current_user)
    return svc.get_settings(module_name)


@router.put("/settings/modules/{module_name}")
async def update_module_settings(
    module_name: str,
    data: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update settings for a specific module."""
    svc = _get_service(db, current_user)
    return svc.update_settings(module_name, data.model_dump(exclude_unset=True))
