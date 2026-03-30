"""API routes for Issues"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_progress.schemas.progress import (
    IssueCreate, IssueUpdate, IssueResponse,
)
from addons.agcm_progress.services.progress_service import ProgressService

router = APIRouter()


def _get_service(db: Session, current_user) -> ProgressService:
    company_id = get_effective_company_id(current_user, db)
    return ProgressService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/issues", response_model=None)
async def list_issues(
    project_id: int = Query(..., description="Filter by project"),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List issues for a project with filtering and pagination."""
    svc = _get_service(db, current_user)
    return svc.list_issues(
        project_id=project_id,
        status=status,
        severity=severity,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/issues/{issue_id}", response_model=None)
async def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get issue details."""
    svc = _get_service(db, current_user)
    issue = svc.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/issues", response_model=None, status_code=201)
async def create_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new issue."""
    svc = _get_service(db, current_user)
    issue = svc.create_issue(data)
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.issue_created(db, issue)
    except Exception:
        pass
    return IssueResponse.model_validate(issue).model_dump()


@router.put("/issues/{issue_id}", response_model=None)
async def update_issue(
    issue_id: int,
    data: IssueUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an issue."""
    svc = _get_service(db, current_user)
    old_issue = svc.get_issue(issue_id)
    old_status = str(old_issue.status) if old_issue and old_issue.status else None
    issue = svc.update_issue(issue_id, data)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        new_status = str(issue.status) if issue.status else None
        if old_status and new_status and old_status != new_status:
            await agcm_realtime.issue_status_changed(db, issue, old_status, new_status)
    except Exception:
        pass
    return IssueResponse.model_validate(issue).model_dump()


@router.delete("/issues/{issue_id}", status_code=204)
async def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an issue."""
    svc = _get_service(db, current_user)
    if not svc.delete_issue(issue_id):
        raise HTTPException(status_code=404, detail="Issue not found")


@router.post("/issues/{issue_id}/resolve", response_model=None)
async def resolve_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark issue as resolved."""
    svc = _get_service(db, current_user)
    issue = svc.resolve_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    try:
        from addons.agcm.services.realtime_events import agcm_realtime
        await agcm_realtime.issue_status_changed(db, issue, "open", "resolved")
    except Exception:
        pass
    return IssueResponse.model_validate(issue).model_dump()


@router.post("/issues/{issue_id}/close", response_model=None)
async def close_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Close an issue."""
    svc = _get_service(db, current_user)
    issue = svc.close_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return IssueResponse.model_validate(issue).model_dump()
