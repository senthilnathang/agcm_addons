"""AGCM Approval API — wraps base_automation approval with entity-specific handlers."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


class ApprovalActionRequest(BaseModel):
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Approve / Reject a task (with entity completion handler)
# ---------------------------------------------------------------------------

@router.post("/approvals/{task_id}/approve")
async def approve_task(
    task_id: int,
    data: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve an AGCM approval task. If the chain completes, updates the entity."""
    try:
        from modules.base_automation.services.approval_service import ApprovalService
        from addons.agcm.services.approval_handlers import on_approval_complete

        svc = ApprovalService(db)
        task, chain_complete, outcome = svc.approve_task(
            task_id=task_id,
            user_id=current_user.id,
            note=data.note,
        )

        if chain_complete and outcome:
            on_approval_complete(
                db=db,
                entity_type=task.entity_type,
                entity_id=task.entity_id,
                user_id=current_user.id,
                outcome=outcome,
            )

        db.commit()

        return {
            "task_id": task.id,
            "status": task.status,
            "chain_complete": chain_complete,
            "outcome": outcome,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
        }

    except ImportError:
        raise HTTPException(status_code=501, detail="Approval module not installed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{task_id}/reject")
async def reject_task(
    task_id: int,
    data: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject an AGCM approval task. Cancels remaining tasks and updates entity."""
    try:
        from modules.base_automation.services.approval_service import ApprovalService
        from addons.agcm.services.approval_handlers import on_approval_complete

        svc = ApprovalService(db)
        task, chain_complete, outcome = svc.reject_task(
            task_id=task_id,
            user_id=current_user.id,
            note=data.note,
        )

        if chain_complete and outcome:
            on_approval_complete(
                db=db,
                entity_type=task.entity_type,
                entity_id=task.entity_id,
                user_id=current_user.id,
                outcome=outcome,
            )

        db.commit()

        return {
            "task_id": task.id,
            "status": task.status,
            "chain_complete": chain_complete,
            "outcome": outcome,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
        }

    except ImportError:
        raise HTTPException(status_code=501, detail="Approval module not installed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Pending approvals for current user
# ---------------------------------------------------------------------------

@router.get("/approvals/pending")
async def list_pending_approvals(
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List pending AGCM approval tasks for the current user."""
    from addons.agcm.services.approval_integration import get_pending_approvals

    company_id = get_effective_company_id(current_user, db)
    return get_pending_approvals(db, current_user.id, company_id, entity_type)


# ---------------------------------------------------------------------------
# Check approval status for an entity
# ---------------------------------------------------------------------------

@router.get("/approvals/entity/{entity_type}/{entity_id}")
async def check_entity_approval(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Check the approval status of an AGCM entity."""
    from addons.agcm.services.approval_integration import check_approval

    status = check_approval(db, entity_type, entity_id)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "approval_status": status or "not_configured",
    }
