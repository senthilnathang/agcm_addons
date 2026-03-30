"""API routes for Tasks and Dependencies"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id, PaginationParams, get_pagination

from addons.agcm_schedule.schemas.schedule import (
    TaskCreate, TaskUpdate, TaskResponse,
    DependencyCreate, DependencyResponse,
)
from addons.agcm_schedule.services.schedule_service import ScheduleService

router = APIRouter()


class ProgressBody(BaseModel):
    progress: int


def _get_service(db: Session, current_user) -> ScheduleService:
    company_id = get_effective_company_id(current_user, db)
    return ScheduleService(db=db, company_id=company_id, user_id=current_user.id)


# =============================================================================
# TASKS
# =============================================================================

@router.get("/tasks", response_model=None)
async def list_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    schedule_id: Optional[int] = Query(None, description="Filter by schedule"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or sequence"),
):
    """List tasks with filtering and pagination."""
    svc = _get_service(db, current_user)
    result = svc.list_tasks(
        project_id=project_id,
        schedule_id=schedule_id,
        status=status,
        search=search,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    result["items"] = [TaskResponse.model_validate(t).model_dump() for t in result["items"]]
    return result


@router.get("/tasks/{task_id}", response_model=None)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single task by ID."""
    svc = _get_service(db, current_user)
    task = svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task).model_dump()


@router.post("/tasks", response_model=None, status_code=201)
async def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new task."""
    svc = _get_service(db, current_user)
    task = svc.create_task(data)
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.task_created(db, task)
    except Exception:
        pass
    return TaskResponse.model_validate(task).model_dump()


@router.put("/tasks/{task_id}", response_model=None)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a task."""
    svc = _get_service(db, current_user)
    old_task = svc.get_task(task_id)
    old_status = str(old_task.status) if old_task and old_task.status else None
    task = svc.update_task(task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        new_status = str(task.status) if task.status else None
        if old_status and new_status and old_status != new_status:
            await agcm_realtime.task_status_changed(db, task, old_status, new_status)
    except Exception:
        pass
    return TaskResponse.model_validate(task).model_dump()


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a task."""
    svc = _get_service(db, current_user)
    if not svc.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/tasks/{task_id}/progress", response_model=None)
async def update_task_progress(
    task_id: int,
    body: ProgressBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update task progress (0-100)."""
    svc = _get_service(db, current_user)
    old_task = svc.get_task(task_id)
    old_progress = old_task.progress if old_task else 0
    task = svc.update_progress(task_id, body.progress)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        if old_progress != body.progress:
            await agcm_realtime.task_progress_changed(db, task, old_progress, body.progress)
    except Exception:
        pass
    return TaskResponse.model_validate(task).model_dump()


# =============================================================================
# DEPENDENCIES
# =============================================================================

@router.get("/dependencies", response_model=None)
async def list_dependencies(
    schedule_id: int = Query(..., description="Schedule ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all dependencies for tasks in a schedule."""
    svc = _get_service(db, current_user)
    items = svc.list_dependencies(schedule_id)
    return {
        "items": [DependencyResponse.model_validate(d).model_dump() for d in items],
        "total": len(items),
    }


@router.post("/dependencies", response_model=None, status_code=201)
async def create_dependency(
    data: DependencyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a task dependency."""
    svc = _get_service(db, current_user)
    dep = svc.create_dependency(data)
    return DependencyResponse.model_validate(dep).model_dump()


@router.delete("/dependencies/{dep_id}", status_code=204)
async def delete_dependency(
    dep_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a dependency."""
    svc = _get_service(db, current_user)
    if not svc.delete_dependency(dep_id):
        raise HTTPException(status_code=404, detail="Dependency not found")
