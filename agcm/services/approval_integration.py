"""
AGCM Approval Integration — wires construction entities into core approval chains.

Uses the core `base_automation` approval system (ApprovalChain, ApprovalStep, ApprovalTask)
for multi-level approval workflows on POs, Change Orders, Subcontracts, and Submittals.

Usage:
    from addons.agcm.services.approval_integration import submit_for_approval, check_approval

    # Submit entity for approval
    tasks = submit_for_approval(db, "purchase_order", po.id, user_id, company_id, amount=po.total_amount)

    # Check if entity is approved
    status = check_approval(db, "purchase_order", po.id)
    # Returns: "pending", "approved", "rejected", or None (no chain configured)

Setup (one-time, via admin UI or seed):
    Create ApprovalChain with entity_type matching AGCM entities:
    - "purchase_order" → PO approval
    - "change_order" → CO approval
    - "subcontract" → Subcontract approval
    - "submittal" → Submittal approval
    - "estimate" → Estimate approval
    - "vendor_bill" → Bill approval
"""

import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Entity types used for approval chain matching
AGCM_ENTITY_TYPES = [
    "purchase_order",
    "change_order",
    "subcontract",
    "submittal",
    "estimate",
    "vendor_bill",
    "proposal",
]


def submit_for_approval(
    db: Session,
    entity_type: str,
    entity_id: int,
    requester_id: int,
    company_id: int,
    amount: Optional[float] = None,
    context_data: Optional[Dict] = None,
) -> Optional[List]:
    """
    Submit a construction entity for approval via the core approval system.

    Looks up a matching ApprovalChain by entity_type (and optionally amount).
    Creates ApprovalTask instances for each step in the chain.

    Returns list of created ApprovalTasks, or None if no chain is configured
    (in which case the entity should be auto-approved).
    """
    try:
        from modules.base_automation.services.approval_service import ApprovalService

        svc = ApprovalService(db)
        tasks = svc.create_approval_request(
            entity_type=entity_type,
            entity_id=entity_id,
            requester_id=requester_id,
            company_id=company_id,
            amount=amount,
            context_data=context_data or {},
        )
        logger.info(
            "Submitted %s #%d for approval: %d tasks created",
            entity_type, entity_id, len(tasks),
        )
        return tasks

    except ValueError as e:
        # No approval chain configured — entity should be auto-approved
        logger.debug("No approval chain for %s: %s", entity_type, e)
        return None

    except ImportError:
        logger.debug("Approval module (base_automation) not installed")
        return None

    except Exception as e:
        logger.warning("Approval submission failed for %s #%d: %s", entity_type, entity_id, e)
        return None


def check_approval(
    db: Session,
    entity_type: str,
    entity_id: int,
) -> Optional[str]:
    """
    Check the approval status of an entity.

    Returns:
        "pending" — approval in progress
        "approved" — all steps approved
        "rejected" — at least one step rejected
        None — no approval chain configured (auto-approved)
    """
    try:
        from modules.base_automation.models.approval import ApprovalTask, TaskStatus

        tasks = ApprovalTask.get_for_entity(db, entity_type, entity_id)
        if not tasks:
            return None

        statuses = [t.status for t in tasks]

        if any(s == TaskStatus.REJECTED.value for s in statuses):
            return "rejected"
        if all(s == TaskStatus.APPROVED.value for s in statuses):
            return "approved"
        return "pending"

    except ImportError:
        return None
    except Exception:
        return None


def get_pending_approvals(
    db: Session,
    user_id: int,
    company_id: int,
    entity_type: Optional[str] = None,
) -> List[Dict]:
    """
    Get all pending AGCM approval tasks for a user.

    Returns list of dicts with task info + entity details.
    """
    try:
        from modules.base_automation.models.approval import ApprovalTask, TaskStatus

        query = db.query(ApprovalTask).filter(
            ApprovalTask.assigned_to_id == user_id,
            ApprovalTask.company_id == company_id,
            ApprovalTask.status == TaskStatus.PENDING.value,
        )

        if entity_type:
            query = query.filter(ApprovalTask.entity_type == entity_type)
        else:
            query = query.filter(ApprovalTask.entity_type.in_(AGCM_ENTITY_TYPES))

        tasks = query.order_by(ApprovalTask.due_at.asc().nullslast()).all()

        return [
            {
                "task_id": t.id,
                "entity_type": t.entity_type,
                "entity_id": t.entity_id,
                "step_name": t.step.name if t.step else f"Step {t.step_order}",
                "step_order": t.step_order,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "is_overdue": t.is_overdue,
                "requester_id": t.requester_id,
                "chain_name": t.chain.name if t.chain else "",
                "context_data": t.context_data or {},
            }
            for t in tasks
        ]

    except ImportError:
        return []
    except Exception:
        return []
