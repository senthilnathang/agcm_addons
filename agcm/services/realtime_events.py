"""
AGCM Real-time Events — per-project WebSocket broadcasting.

Thin wrapper around the core RealtimeService that provides AGCM-specific
event publishing. All events flow through the core WebSocket infrastructure.

Usage in API endpoints:
    from addons.agcm.services.realtime_events import agcm_realtime

    # After updating a project:
    await agcm_realtime.project_updated(db, project)

    # After creating an RFI response:
    await agcm_realtime.rfi_response_created(db, rfi, response)

    # After approving a submittal:
    await agcm_realtime.submittal_status_changed(db, submittal, "approved")

Frontend subscription (in SFC views):
    const { on } = useRealtime();
    on('agcm:project:updated', (data) => { ... });
    on('agcm:rfi:response_new', (data) => { ... });
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event type constants — used as WebSocket message "type" field
# ---------------------------------------------------------------------------

class AGCMEvent:
    # Project
    PROJECT_CREATED = "agcm:project:created"
    PROJECT_UPDATED = "agcm:project:updated"
    PROJECT_STATUS_CHANGED = "agcm:project:status_changed"
    PROJECT_DELETED = "agcm:project:deleted"

    # Daily Log
    DAILYLOG_CREATED = "agcm:dailylog:created"
    DAILYLOG_UPDATED = "agcm:dailylog:updated"

    # RFI
    RFI_CREATED = "agcm:rfi:created"
    RFI_UPDATED = "agcm:rfi:updated"
    RFI_STATUS_CHANGED = "agcm:rfi:status_changed"
    RFI_RESPONSE_NEW = "agcm:rfi:response_new"
    RFI_CLOSED = "agcm:rfi:closed"

    # Submittal
    SUBMITTAL_CREATED = "agcm:submittal:created"
    SUBMITTAL_STATUS_CHANGED = "agcm:submittal:status_changed"
    SUBMITTAL_APPROVED = "agcm:submittal:approved"
    SUBMITTAL_REJECTED = "agcm:submittal:rejected"

    # Change Order
    CO_CREATED = "agcm:changeorder:created"
    CO_STATUS_CHANGED = "agcm:changeorder:status_changed"
    CO_APPROVED = "agcm:changeorder:approved"

    # Schedule / Tasks
    TASK_CREATED = "agcm:task:created"
    TASK_UPDATED = "agcm:task:updated"
    TASK_PROGRESS_CHANGED = "agcm:task:progress_changed"
    TASK_STATUS_CHANGED = "agcm:task:status_changed"

    # Issues
    ISSUE_CREATED = "agcm:issue:created"
    ISSUE_UPDATED = "agcm:issue:updated"
    ISSUE_STATUS_CHANGED = "agcm:issue:status_changed"
    ISSUE_RESOLVED = "agcm:issue:resolved"

    # Documents
    DOCUMENT_UPLOADED = "agcm:document:uploaded"
    DOCUMENT_STATUS_CHANGED = "agcm:document:status_changed"

    # Finance
    INVOICE_CREATED = "agcm:invoice:created"
    INVOICE_PAID = "agcm:invoice:paid"
    BILL_CREATED = "agcm:bill:created"
    EXPENSE_CREATED = "agcm:expense:created"

    # Milestones
    MILESTONE_COMPLETED = "agcm:milestone:completed"


def _get_realtime():
    """Lazy import to avoid circular deps and graceful fallback."""
    try:
        from app.services.realtime import realtime
        return realtime
    except Exception:
        return None


def _get_project_user_ids(db, project_id: int) -> List[int]:
    """Get all user IDs assigned to a project (for targeted broadcast)."""
    try:
        from sqlalchemy import text
        rows = db.execute(
            text("SELECT user_id FROM agcm_project_users WHERE project_id = :pid"),
            {"pid": project_id},
        ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


class AGCMRealtime:
    """
    AGCM-specific real-time event publisher.

    All methods are fire-and-forget (best effort).
    If WebSocket is unavailable, events are silently dropped.
    """

    # ------------------------------------------------------------------
    # Core broadcast helper
    # ------------------------------------------------------------------

    async def _publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_ids: Optional[List[int]] = None,
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Publish an event to targeted users via WebSocket."""
        rt = _get_realtime()
        if not rt:
            return 0

        try:
            message = {"type": event_type, "data": data}

            if user_ids:
                exclude = [exclude_user_id] if exclude_user_id else None
                result = await rt.publish(
                    event_type=event_type,
                    data=data,
                    user_ids=user_ids,
                    exclude_user_ids=exclude,
                )
                count = sum(result.values()) if isinstance(result, dict) else 0
            else:
                # Broadcast to all — rare, only for system events
                from app.core.websocket import manager
                count = await manager.broadcast_to_all(message)

            logger.debug("AGCM event %s → %d recipients", event_type, count)
            return count

        except Exception as e:
            logger.warning("AGCM realtime publish failed: %s", e)
            return 0

    async def _publish_to_project(
        self,
        db,
        project_id: int,
        event_type: str,
        data: Dict[str, Any],
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Publish event to all users assigned to a project."""
        user_ids = _get_project_user_ids(db, project_id)
        if not user_ids:
            return 0
        data["project_id"] = project_id
        return await self._publish(event_type, data, user_ids, exclude_user_id)

    # ------------------------------------------------------------------
    # Project events
    # ------------------------------------------------------------------

    async def project_created(self, db, project) -> int:
        return await self._publish_to_project(db, project.id, AGCMEvent.PROJECT_CREATED, {
            "id": project.id,
            "name": project.name,
            "sequence_name": project.sequence_name,
            "status": str(project.status) if project.status else None,
        })

    async def project_updated(self, db, project, changed_fields: Optional[List[str]] = None) -> int:
        return await self._publish_to_project(db, project.id, AGCMEvent.PROJECT_UPDATED, {
            "id": project.id,
            "name": project.name,
            "changed_fields": changed_fields or [],
        })

    async def project_status_changed(self, db, project, old_status: str, new_status: str) -> int:
        return await self._publish_to_project(db, project.id, AGCMEvent.PROJECT_STATUS_CHANGED, {
            "id": project.id,
            "name": project.name,
            "old_status": old_status,
            "new_status": new_status,
        })

    # ------------------------------------------------------------------
    # Daily Log events
    # ------------------------------------------------------------------

    async def dailylog_created(self, db, log) -> int:
        return await self._publish_to_project(db, log.project_id, AGCMEvent.DAILYLOG_CREATED, {
            "id": log.id,
            "date": str(log.date) if log.date else None,
            "sequence_name": log.sequence_name,
        })

    async def dailylog_updated(self, db, log) -> int:
        return await self._publish_to_project(db, log.project_id, AGCMEvent.DAILYLOG_UPDATED, {
            "id": log.id,
            "date": str(log.date) if log.date else None,
        })

    # ------------------------------------------------------------------
    # RFI events
    # ------------------------------------------------------------------

    async def rfi_created(self, db, rfi) -> int:
        return await self._publish_to_project(db, rfi.project_id, AGCMEvent.RFI_CREATED, {
            "id": rfi.id,
            "subject": rfi.subject,
            "sequence_name": rfi.sequence_name,
            "priority": str(rfi.priority) if rfi.priority else None,
        })

    async def rfi_status_changed(self, db, rfi, old_status: str, new_status: str) -> int:
        return await self._publish_to_project(db, rfi.project_id, AGCMEvent.RFI_STATUS_CHANGED, {
            "id": rfi.id,
            "subject": rfi.subject,
            "old_status": old_status,
            "new_status": new_status,
        })

    async def rfi_response_created(self, db, rfi, response) -> int:
        return await self._publish_to_project(
            db, rfi.project_id, AGCMEvent.RFI_RESPONSE_NEW,
            {
                "rfi_id": rfi.id,
                "rfi_subject": rfi.subject,
                "response_id": response.id,
                "is_official": getattr(response, "is_official_response", False),
                "responded_by": response.responded_by,
            },
            exclude_user_id=response.responded_by,
        )

    async def rfi_closed(self, db, rfi) -> int:
        return await self._publish_to_project(db, rfi.project_id, AGCMEvent.RFI_CLOSED, {
            "id": rfi.id,
            "subject": rfi.subject,
        })

    # ------------------------------------------------------------------
    # Submittal events
    # ------------------------------------------------------------------

    async def submittal_created(self, db, submittal) -> int:
        return await self._publish_to_project(db, submittal.project_id, AGCMEvent.SUBMITTAL_CREATED, {
            "id": submittal.id,
            "title": submittal.title,
            "sequence_name": submittal.sequence_name,
        })

    async def submittal_status_changed(self, db, submittal, old_status: str, new_status: str) -> int:
        event = AGCMEvent.SUBMITTAL_STATUS_CHANGED
        if new_status == "approved":
            event = AGCMEvent.SUBMITTAL_APPROVED
        elif new_status == "rejected":
            event = AGCMEvent.SUBMITTAL_REJECTED
        return await self._publish_to_project(db, submittal.project_id, event, {
            "id": submittal.id,
            "title": submittal.title,
            "old_status": old_status,
            "new_status": new_status,
        })

    # ------------------------------------------------------------------
    # Change Order events
    # ------------------------------------------------------------------

    async def change_order_created(self, db, co) -> int:
        return await self._publish_to_project(db, co.project_id, AGCMEvent.CO_CREATED, {
            "id": co.id,
            "title": co.title,
            "sequence_name": co.sequence_name,
            "cost_impact": float(co.cost_impact) if co.cost_impact else 0,
        })

    async def change_order_status_changed(self, db, co, old_status: str, new_status: str) -> int:
        event = AGCMEvent.CO_APPROVED if new_status == "approved" else AGCMEvent.CO_STATUS_CHANGED
        return await self._publish_to_project(db, co.project_id, event, {
            "id": co.id,
            "title": co.title,
            "old_status": old_status,
            "new_status": new_status,
        })

    # ------------------------------------------------------------------
    # Task events
    # ------------------------------------------------------------------

    async def task_created(self, db, task) -> int:
        return await self._publish_to_project(db, task.project_id, AGCMEvent.TASK_CREATED, {
            "id": task.id,
            "name": task.name,
            "sequence_name": task.sequence_name,
        })

    async def task_progress_changed(self, db, task, old_progress: int, new_progress: int) -> int:
        return await self._publish_to_project(db, task.project_id, AGCMEvent.TASK_PROGRESS_CHANGED, {
            "id": task.id,
            "name": task.name,
            "old_progress": old_progress,
            "new_progress": new_progress,
        })

    async def task_status_changed(self, db, task, old_status: str, new_status: str) -> int:
        return await self._publish_to_project(db, task.project_id, AGCMEvent.TASK_STATUS_CHANGED, {
            "id": task.id,
            "name": task.name,
            "old_status": old_status,
            "new_status": new_status,
        })

    # ------------------------------------------------------------------
    # Issue events
    # ------------------------------------------------------------------

    async def issue_created(self, db, issue) -> int:
        return await self._publish_to_project(db, issue.project_id, AGCMEvent.ISSUE_CREATED, {
            "id": issue.id,
            "title": issue.title,
            "sequence_name": issue.sequence_name,
            "severity": str(issue.severity) if issue.severity else None,
        })

    async def issue_status_changed(self, db, issue, old_status: str, new_status: str) -> int:
        event = AGCMEvent.ISSUE_RESOLVED if new_status == "resolved" else AGCMEvent.ISSUE_STATUS_CHANGED
        return await self._publish_to_project(db, issue.project_id, event, {
            "id": issue.id,
            "title": issue.title,
            "old_status": old_status,
            "new_status": new_status,
        })

    # ------------------------------------------------------------------
    # Document events
    # ------------------------------------------------------------------

    async def document_uploaded(self, db, document) -> int:
        return await self._publish_to_project(db, document.project_id, AGCMEvent.DOCUMENT_UPLOADED, {
            "id": document.id,
            "name": document.name,
            "document_type": str(document.document_type) if document.document_type else None,
        })

    # ------------------------------------------------------------------
    # Finance events
    # ------------------------------------------------------------------

    async def invoice_created(self, db, invoice) -> int:
        return await self._publish_to_project(db, invoice.project_id, AGCMEvent.INVOICE_CREATED, {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
        })

    async def invoice_paid(self, db, invoice) -> int:
        return await self._publish_to_project(db, invoice.project_id, AGCMEvent.INVOICE_PAID, {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
        })

    # ------------------------------------------------------------------
    # Milestone events
    # ------------------------------------------------------------------

    async def milestone_completed(self, db, milestone) -> int:
        return await self._publish_to_project(db, milestone.project_id, AGCMEvent.MILESTONE_COMPLETED, {
            "id": milestone.id,
            "name": milestone.name,
        })


# Module-level singleton
agcm_realtime = AGCMRealtime()
