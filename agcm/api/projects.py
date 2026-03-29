"""API routes for Project"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id, PaginationParams, get_pagination

from addons.agcm.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail
from addons.agcm.services.project_service import ProjectService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProjectService:
    company_id = get_effective_company_id(current_user, db)
    return ProjectService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/projects", response_model=None)
async def list_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    status: Optional[str] = Query(None, description="Filter by status: new, inprogress, completed"),
    search: Optional[str] = Query(None, description="Search by name, ref_number, or sequence"),
):
    """List construction projects with pagination and filtering."""
    svc = _get_service(db, current_user)
    result = svc.list_projects(
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        search=search,
        is_management=current_user.is_superuser,
    )
    return result


@router.get("/projects/{project_id}", response_model=None)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get project details with related data."""
    svc = _get_service(db, current_user)
    detail = svc.get_project_detail(project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.post("/projects", response_model=None, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new construction project."""
    svc = _get_service(db, current_user)
    project = svc.create_project(data)
    return ProjectResponse.model_validate(project).model_dump()


@router.put("/projects/{project_id}", response_model=None)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a project."""
    svc = _get_service(db, current_user)
    project = svc.update_project(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project).model_dump()


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Soft-delete a project."""
    svc = _get_service(db, current_user)
    if not svc.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
