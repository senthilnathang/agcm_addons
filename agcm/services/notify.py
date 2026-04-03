"""
AGCM Centralized Notification Engine.

Single entry point for all construction module notifications.
Dispatches via core notification_service (in-app + email) with safe fallbacks.

Usage:
    from addons.agcm.services.notify import notify_event

    notify_event(
        db, event_type="created", entity_type="rfi", entity_id=rfi.id,
        actor_id=user_id, context={"subject": rfi.subject},
        recipient_ids=[project_manager_id], company_id=company_id,
    )
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event Type Registry — maps entity.event → notification config
# ---------------------------------------------------------------------------

AGCM_EVENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # RFI
    "rfi.created": {
        "title": "New RFI: {subject}",
        "description": "A new RFI has been opened on project {project_name}",
        "level": "info",
        "channels": ["in_app", "email"],
    },
    "rfi.response_added": {
        "title": "RFI Response: {subject}",
        "description": "A new response was added to RFI {sequence_name}",
        "level": "info",
        "channels": ["in_app", "email"],
    },
    "rfi.closed": {
        "title": "RFI Closed: {subject}",
        "description": "RFI {sequence_name} has been closed",
        "level": "success",
        "channels": ["in_app"],
    },
    # Submittal
    "submittal.approved": {
        "title": "Submittal Approved: {title}",
        "description": "Submittal {sequence_name} has been approved",
        "level": "success",
        "channels": ["in_app", "email"],
    },
    "submittal.rejected": {
        "title": "Submittal Rejected: {title}",
        "description": "Submittal {sequence_name} has been rejected",
        "level": "error",
        "channels": ["in_app", "email"],
    },
    # Change Order
    "change_order.approved": {
        "title": "Change Order Approved: {title}",
        "description": "CO {sequence_name} approved — cost impact: ${cost_impact}",
        "level": "success",
        "channels": ["in_app", "email"],
    },
    "change_order.rejected": {
        "title": "Change Order Rejected: {title}",
        "description": "CO {sequence_name} has been rejected",
        "level": "error",
        "channels": ["in_app", "email"],
    },
    # Tasks
    "task.assigned": {
        "title": "Task Assigned: {name}",
        "description": "You have been assigned a new task on project {project_name}",
        "level": "info",
        "channels": ["in_app", "email"],
    },
    "task.due_soon": {
        "title": "Task Due Soon: {name}",
        "description": "Task {name} is due on {due_date}",
        "level": "warning",
        "channels": ["in_app"],
    },
    # Purchase Order
    "purchase_order.approved": {
        "title": "PO Approved: {po_number}",
        "description": "Purchase Order {sequence_name} has been approved",
        "level": "success",
        "channels": ["in_app", "email"],
    },
    "purchase_order.pending_approval": {
        "title": "PO Pending Approval: {po_number}",
        "description": "Purchase Order {sequence_name} requires your approval",
        "level": "warning",
        "channels": ["in_app", "email"],
    },
    # Safety
    "inspection.completed": {
        "title": "Inspection Complete: {description}",
        "description": "Safety inspection completed on project {project_name}",
        "level": "info",
        "channels": ["in_app"],
    },
    "incident.reported": {
        "title": "Incident Reported: {description}",
        "description": "A safety incident has been reported on project {project_name}",
        "level": "error",
        "channels": ["in_app", "email"],
    },
    "punch_list.assigned": {
        "title": "Punch List Item: {description}",
        "description": "You have been assigned a punch list item",
        "level": "info",
        "channels": ["in_app"],
    },
    # Timesheet
    "timesheet.approved": {
        "title": "Timesheet Approved",
        "description": "Your timesheet for {date} has been approved",
        "level": "success",
        "channels": ["in_app"],
    },
    "timesheet.rejected": {
        "title": "Timesheet Rejected",
        "description": "Your timesheet for {date} has been rejected",
        "level": "error",
        "channels": ["in_app"],
    },
    # Budget
    "budget.threshold_warning": {
        "title": "Budget Alert: {description}",
        "description": "Project {project_name} budget is {pct_spent}% spent",
        "level": "warning",
        "channels": ["in_app", "email"],
    },
    # Daily Log
    "daily_log.not_submitted": {
        "title": "Daily Log Reminder",
        "description": "Daily log for {date} on project {project_name} has not been submitted",
        "level": "warning",
        "channels": ["in_app"],
    },
}


def _format_template(template: str, context: Dict[str, Any]) -> str:
    """Safe string format with fallback for missing keys."""
    try:
        return template.format(**context)
    except (KeyError, IndexError):
        return template


def notify_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: int,
    actor_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    recipient_ids: Optional[List[int]] = None,
    company_id: Optional[int] = None,
) -> bool:
    """
    Dispatch a notification for an AGCM entity event.

    Args:
        db: Database session
        event_type: Event name (e.g., "created", "approved", "assigned")
        entity_type: Entity name (e.g., "rfi", "change_order", "task")
        entity_id: Entity record ID
        actor_id: User who triggered the event
        context: Template variables for title/description
        recipient_ids: List of user IDs to notify
        company_id: Company scope

    Returns:
        True if dispatched to at least one recipient, False otherwise.
    """
    if not recipient_ids:
        logger.debug("notify_event: no recipients for %s.%s#%d", entity_type, event_type, entity_id)
        return False

    ctx = context or {}
    event_key = f"{entity_type}.{event_type}"
    config = AGCM_EVENT_REGISTRY.get(event_key, {})

    title = _format_template(config.get("title", f"{entity_type} {event_type}"), ctx)
    description = _format_template(config.get("description", ""), ctx)
    level = config.get("level", "info")
    channels = config.get("channels", ["in_app"])

    dispatched = 0

    for user_id in recipient_ids:
        if user_id == actor_id:
            continue  # Don't notify the actor about their own action

        try:
            # Try core notification service first
            _dispatch_via_core(
                db, user_id, event_key, title, description, level,
                channels, entity_type, entity_id, actor_id, company_id, ctx,
            )
            dispatched += 1
        except Exception as e:
            # Fallback: try WebSocket in-app only
            try:
                _dispatch_in_app_fallback(db, user_id, title, description, level)
                dispatched += 1
            except Exception:
                logger.warning(
                    "notify_event: all channels failed for user %d on %s: %s",
                    user_id, event_key, e,
                )

    if dispatched > 0:
        logger.info(
            "notify_event: %s → %d/%d recipients",
            event_key, dispatched, len(recipient_ids),
        )
    return dispatched > 0


def _dispatch_via_core(
    db, user_id, type_code, title, description, level,
    channels, entity_type, entity_id, actor_id, company_id, context,
):
    """Dispatch via core notification_service (multi-channel)."""
    try:
        from modules.notification.services.notification_service import notification_service

        notification_service.create(
            db=db,
            user_id=user_id,
            type_code=type_code,
            context=context,
            title=title,
            description=description,
            level=level,
            actor_id=actor_id,
            channels=channels,
            source_event=type_code,
            source_model=f"agcm_{entity_type}",
            source_id=entity_id,
            company_id=company_id,
        )
    except ImportError:
        raise  # Let caller try fallback
    except Exception as e:
        logger.debug("Core notification dispatch failed: %s", e)
        raise


def _dispatch_in_app_fallback(db, user_id, title, description, level):
    """Fallback: WebSocket broadcast only (no email)."""
    try:
        from app.core.websocket import manager

        manager.broadcast_to_user(user_id, {
            "type": "notification:new",
            "data": {
                "title": title,
                "description": description,
                "level": level,
                "is_read": False,
            },
        })
    except ImportError:
        pass  # No WebSocket available
    except Exception:
        pass  # Best effort
