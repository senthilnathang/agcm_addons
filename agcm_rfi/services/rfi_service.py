"""RFI service - business logic for RFIs and responses"""

import logging
import re
from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_rfi.models.rfi import (
    RFI,
    RFILabel,
    agcm_rfi_label_rel,
    agcm_rfi_assignees,
)
from addons.agcm_rfi.models.rfi_response import RFIResponse
from addons.agcm_rfi.schemas.rfi import (
    RFICreate,
    RFIUpdate,
    RFIResponseCreate,
    RFIResponseUpdate,
)

try:
    from app.core.cache import cache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

SEQUENCE_PREFIX = "RFI"
SEQUENCE_PADDING = 5


def _next_rfi_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(RFI.sequence_name)
        .filter(RFI.company_id == company_id, RFI.sequence_name.isnot(None))
        .order_by(RFI.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r"(\d+)$", last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


class RFIService:
    """Handles RFI CRUD, status workflow, and response management."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # --- RFI CRUD ---

    def list_rfis(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(RFI).filter(
            RFI.company_id == self.company_id,
        )
        if not include_deleted:
            query = query.filter(RFI.is_deleted == False)

        if project_id:
            query = query.filter(RFI.project_id == project_id)
        if status:
            query = query.filter(RFI.status == status)
        if priority:
            query = query.filter(RFI.priority == priority)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (RFI.subject.ilike(term)) | (RFI.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(RFI.id.desc()).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_rfi(self, rfi_id: int, include_deleted: bool = False) -> Optional[RFI]:
        query = self.db.query(RFI).filter(
            RFI.id == rfi_id,
            RFI.company_id == self.company_id,
        )
        if not include_deleted:
            query = query.filter(RFI.is_deleted == False)
        return query.first()

    def _get_rfi_detail_uncached(self, rfi_id: int) -> Optional[dict]:
        """Internal method to get RFI detail without caching."""
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None

        response_count = (
            self.db.query(func.count(RFIResponse.id))
            .filter(RFIResponse.rfi_id == rfi_id)
            .scalar()
            or 0
        )

        responses = (
            self.db.query(RFIResponse)
            .filter(RFIResponse.rfi_id == rfi_id)
            .order_by(RFIResponse.created_at)
            .all()
        )

        response_dicts = [
            {
                "id": r.id,
                "rfi_id": r.rfi_id,
                "parent_id": r.parent_id,
                "content": r.content,
                "is_official_response": r.is_official_response,
                "responded_by": r.responded_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in responses
        ]

        result = {}
        for c in rfi.__table__.columns:
            val = getattr(rfi, c.key, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            result[c.key] = val

        return {
            **result,
            "assignee_ids": [u.id for u in rfi.assignees],
            "label_ids": [l.id for l in rfi.labels],
            "labels": [
                {"id": l.id, "name": l.name, "color": l.color} for l in rfi.labels
            ],
            "response_count": response_count,
            "responses": response_dicts,
        }

    def get_rfi_detail(self, rfi_id: int) -> Optional[dict]:
        """Get RFI detail with related data (cached)."""
        cache_key = f"agcm_rfi:detail:{self.company_id}:{rfi_id}"

        if CACHE_AVAILABLE:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        detail = self._get_rfi_detail_uncached(rfi_id)

        if detail and CACHE_AVAILABLE:
            cache.set(cache_key, detail, ttl=300)

        return detail

    def _invalidate_rfi_cache(self, rfi_id: int = None, project_id: int = None):
        """Invalidate RFI-related cache."""
        if not CACHE_AVAILABLE:
            return

        if rfi_id:
            cache.invalidate(f"agcm_rfi:detail:{self.company_id}:{rfi_id}")

        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_rfi:list:{self.company_id}:project:{project_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_rfi:list:{self.company_id}:*")

    def create_rfi(self, data: RFICreate) -> RFI:
        rfi = RFI(
            company_id=self.company_id,
            sequence_name=_next_rfi_sequence(self.db, self.company_id),
            subject=data.subject,
            question=data.question,
            priority=data.priority or "medium",
            status=data.status or "draft",
            schedule_impact_days=data.schedule_impact_days or 0,
            cost_impact=data.cost_impact or 0.0,
            due_date=data.due_date,
            project_id=data.project_id,
            created_by_user_id=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(rfi)
        self.db.flush()

        if data.assignee_ids:
            self._sync_assignees(rfi.id, set(data.assignee_ids))
        if data.label_ids:
            self._sync_labels(rfi.id, set(data.label_ids))

        self.db.commit()
        self.db.refresh(rfi)

        self._invalidate_rfi_cache(project_id=data.project_id)
        return rfi

    def update_rfi(self, rfi_id: int, data: RFIUpdate) -> Optional[RFI]:
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None

        update_data = data.model_dump(exclude_unset=True)
        assignee_ids = update_data.pop("assignee_ids", None)
        label_ids = update_data.pop("label_ids", None)

        for key, value in update_data.items():
            setattr(rfi, key, value)
        rfi.updated_by = self.user_id

        if assignee_ids is not None:
            self._sync_assignees(rfi.id, set(assignee_ids))
        if label_ids is not None:
            self._sync_labels(rfi.id, set(label_ids))

        self.db.commit()
        self.db.refresh(rfi)

        self._invalidate_rfi_cache(rfi_id=rfi.id, project_id=rfi.project_id)
        return rfi

    def delete_rfi(self, rfi_id: int) -> bool:
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return False
        project_id = rfi.project_id
        rfi.soft_delete(user_id=self.user_id)
        self.db.commit()
        self._invalidate_rfi_cache(rfi_id=rfi_id, project_id=project_id)
        return True

    def restore_rfi(self, rfi_id: int) -> Optional[RFI]:
        rfi = self.get_rfi(rfi_id, include_deleted=True)
        if not rfi or not rfi.is_deleted:
            return None
        rfi.restore()
        self.db.commit()
        self.db.refresh(rfi)
        self._invalidate_rfi_cache(rfi_id=rfi.id, project_id=rfi.project_id)
        return rfi

    def close_rfi(self, rfi_id: int) -> Optional[RFI]:
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None
        rfi.status = "closed"
        rfi.closed_date = date.today()
        rfi.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(rfi)
        self._invalidate_rfi_cache(rfi_id=rfi_id, project_id=rfi.project_id)
        return rfi

    def reopen_rfi(self, rfi_id: int) -> Optional[RFI]:
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None
        rfi.status = "open"
        rfi.closed_date = None
        rfi.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(rfi)
        self._invalidate_rfi_cache(rfi_id=rfi_id, project_id=rfi.project_id)
        return rfi

    # --- RFI → Change Order ---

    def create_change_order_from_rfi(self, rfi_id: int) -> Optional[dict]:
        """Create a draft Change Order pre-populated from an RFI's cost/schedule impact."""
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None

        try:
            from addons.agcm_change_order.services.change_order_service import ChangeOrderService
            from addons.agcm_change_order.schemas.change_order import ChangeOrderCreate

            co_data = ChangeOrderCreate(
                title=rfi.subject or f"Change Order from {rfi.sequence_name}",
                description=rfi.question or "",
                reason=f"Change Order from RFI {rfi.sequence_name}",
                cost_impact=rfi.cost_impact or 0.0,
                schedule_impact_days=rfi.schedule_impact_days or 0,
                project_id=rfi.project_id,
                lines=[],
            )

            co_svc = ChangeOrderService(self.db, self.company_id, self.user_id)
            co = co_svc.create_change_order(co_data)

            return {
                "change_order_id": co.id,
                "sequence_name": co.sequence_name,
                "title": co.title,
                "cost_impact": co.cost_impact,
                "schedule_impact_days": co.schedule_impact_days,
                "status": co.status,
            }

        except ImportError:
            logger.warning("agcm_change_order not installed — cannot create CO from RFI")
            return None

    # --- Responses ---

    def create_response(
        self, rfi_id: int, data: RFIResponseCreate
    ) -> Optional[RFIResponse]:
        rfi = self.get_rfi(rfi_id)
        if not rfi:
            return None

        resp = RFIResponse(
            company_id=self.company_id,
            rfi_id=rfi_id,
            parent_id=data.parent_id,
            content=data.content,
            is_official_response=data.is_official_response or False,
            responded_by=self.user_id,
        )
        self.db.add(resp)

        # Auto-advance status if still draft/open
        if rfi.status in ("draft", "open"):
            rfi.status = "in_progress"

        self.db.commit()
        self.db.refresh(resp)

        self._invalidate_rfi_cache(rfi_id=rfi_id, project_id=rfi.project_id)
        return resp

    def update_response(
        self, response_id: int, data: RFIResponseUpdate
    ) -> Optional[RFIResponse]:
        resp = (
            self.db.query(RFIResponse)
            .filter(
                RFIResponse.id == response_id, RFIResponse.company_id == self.company_id
            )
            .first()
        )
        if not resp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resp, key, value)

        self.db.commit()
        self.db.refresh(resp)

        self._invalidate_rfi_cache(rfi_id=resp.rfi_id)
        return resp

    # --- Labels ---

    def list_labels(self) -> List[RFILabel]:
        return (
            self.db.query(RFILabel)
            .filter(RFILabel.company_id == self.company_id)
            .order_by(RFILabel.name)
            .all()
        )

    def create_label(self, name: str, color: str = "#1890ff") -> RFILabel:
        label = RFILabel(name=name, color=color, company_id=self.company_id)
        self.db.add(label)
        self.db.commit()
        self.db.refresh(label)
        return label

    def delete_label(self, label_id: int) -> bool:
        label = (
            self.db.query(RFILabel)
            .filter(RFILabel.id == label_id, RFILabel.company_id == self.company_id)
            .first()
        )
        if not label:
            return False
        self.db.delete(label)
        self.db.commit()
        return True

    # --- M2M helpers ---

    def _sync_assignees(self, rfi_id: int, user_ids: set):
        self.db.execute(
            agcm_rfi_assignees.delete().where(agcm_rfi_assignees.c.rfi_id == rfi_id)
        )
        for uid in user_ids:
            self.db.execute(
                agcm_rfi_assignees.insert().values(rfi_id=rfi_id, user_id=uid)
            )

    def _sync_labels(self, rfi_id: int, label_ids: set):
        self.db.execute(
            agcm_rfi_label_rel.delete().where(agcm_rfi_label_rel.c.rfi_id == rfi_id)
        )
        for lid in label_ids:
            self.db.execute(
                agcm_rfi_label_rel.insert().values(rfi_id=rfi_id, label_id=lid)
            )
