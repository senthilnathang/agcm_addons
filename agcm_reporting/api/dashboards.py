"""API routes for Dashboard Layouts, Widgets, and KPIs"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_reporting.schemas.dashboard_widget import (
    DashboardLayoutCreate, DashboardLayoutUpdate, DashboardLayoutResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse,
)
from addons.agcm_reporting.services.reporting_service import ReportingService

router = APIRouter()


def _get_service(db: Session, current_user) -> ReportingService:
    company_id = get_effective_company_id(current_user, db)
    return ReportingService(db=db, company_id=company_id, user_id=current_user.id)


# --- Layouts ---

@router.get("/dashboard-layouts", response_model=None)
async def list_layouts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    layout_type: Optional[str] = Query(None),
):
    """List dashboard layouts with pagination."""
    svc = _get_service(db, current_user)
    return svc.list_layouts(page=page, page_size=page_size, layout_type=layout_type)


@router.get("/dashboard-layouts/default", response_model=None)
async def get_default_layout(
    layout_type: str = Query("executive"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get default dashboard layout for a type."""
    svc = _get_service(db, current_user)
    layout = svc.get_default_layout(layout_type)
    if not layout:
        return {"widgets": [], "name": f"Default {layout_type}", "layout_type": layout_type}
    return DashboardLayoutResponse.model_validate(layout).model_dump()


@router.get("/dashboard-layouts/{layout_id}", response_model=None)
async def get_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dashboard layout with widgets."""
    svc = _get_service(db, current_user)
    layout = svc.get_layout(layout_id)
    if not layout:
        raise HTTPException(status_code=404, detail="Layout not found")
    return DashboardLayoutResponse.model_validate(layout).model_dump()


@router.post("/dashboard-layouts", response_model=None, status_code=201)
async def create_layout(
    data: DashboardLayoutCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a dashboard layout with optional widgets."""
    svc = _get_service(db, current_user)
    layout = svc.create_layout(data)
    return DashboardLayoutResponse.model_validate(layout).model_dump()


@router.put("/dashboard-layouts/{layout_id}", response_model=None)
async def update_layout(
    layout_id: int,
    data: DashboardLayoutUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a dashboard layout."""
    svc = _get_service(db, current_user)
    layout = svc.update_layout(layout_id, data)
    if not layout:
        raise HTTPException(status_code=404, detail="Layout not found")
    return DashboardLayoutResponse.model_validate(layout).model_dump()


@router.delete("/dashboard-layouts/{layout_id}", status_code=204)
async def delete_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a dashboard layout."""
    svc = _get_service(db, current_user)
    if not svc.delete_layout(layout_id):
        raise HTTPException(status_code=404, detail="Layout not found")


# --- Widgets ---

@router.post("/dashboard-layouts/{layout_id}/widgets", response_model=None, status_code=201)
async def create_widget(
    layout_id: int,
    data: DashboardWidgetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a widget to a layout."""
    svc = _get_service(db, current_user)
    widget = svc.create_widget(layout_id, data)
    if not widget:
        raise HTTPException(status_code=404, detail="Layout not found")
    return DashboardWidgetResponse.model_validate(widget).model_dump()


@router.put("/widgets/{widget_id}", response_model=None)
async def update_widget(
    widget_id: int,
    data: DashboardWidgetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a dashboard widget."""
    svc = _get_service(db, current_user)
    widget = svc.update_widget(widget_id, data)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return DashboardWidgetResponse.model_validate(widget).model_dump()


@router.delete("/widgets/{widget_id}", status_code=204)
async def delete_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a dashboard widget."""
    svc = _get_service(db, current_user)
    if not svc.delete_widget(widget_id):
        raise HTTPException(status_code=404, detail="Widget not found")


# --- KPIs ---

@router.get("/kpis/portfolio", response_model=None)
async def portfolio_kpis(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get portfolio-level KPIs across all projects."""
    svc = _get_service(db, current_user)
    return svc.get_portfolio_kpis()


@router.get("/kpis/project/{project_id}", response_model=None)
async def project_kpis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get project-level KPIs."""
    svc = _get_service(db, current_user)
    return svc.get_project_kpis(project_id)


@router.get("/kpis/financial/{project_id}", response_model=None)
async def financial_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get financial summary for a project."""
    svc = _get_service(db, current_user)
    return svc.get_financial_summary(project_id)
