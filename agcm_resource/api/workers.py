"""API routes for Workers"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_resource.schemas.resource import WorkerCreate, WorkerUpdate, WorkerResponse
from addons.agcm_resource.services.resource_service import ResourceService

router = APIRouter()


def _get_service(db: Session, current_user) -> ResourceService:
    company_id = get_effective_company_id(current_user, db)
    return ResourceService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/workers", response_model=None)
async def list_workers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, on_leave"),
    trade: Optional[str] = Query(None, description="Filter by trade"),
    search: Optional[str] = Query(None, description="Search by name, sequence, or trade"),
):
    """List workers with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_workers(page=page, page_size=page_size, status=status, trade=trade, search=search)


@router.get("/workers/{worker_id}", response_model=None)
async def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get worker details."""
    svc = _get_service(db, current_user)
    worker = svc.get_worker(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker).model_dump()


@router.post("/workers", response_model=None, status_code=201)
async def create_worker(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new worker."""
    svc = _get_service(db, current_user)
    worker = svc.create_worker(data)
    return WorkerResponse.model_validate(worker).model_dump()


@router.put("/workers/{worker_id}", response_model=None)
async def update_worker(
    worker_id: int,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a worker."""
    svc = _get_service(db, current_user)
    worker = svc.update_worker(worker_id, data)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker).model_dump()


@router.delete("/workers/{worker_id}", status_code=204)
async def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a worker."""
    svc = _get_service(db, current_user)
    if not svc.delete_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker not found")
