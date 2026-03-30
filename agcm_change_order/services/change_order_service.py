"""Change Order service - business logic for change orders and line items"""

import logging
import re
from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_change_order.models.change_order import ChangeOrder, ChangeOrderLine
from addons.agcm_change_order.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderUpdate,
    ChangeOrderLineCreate,
    ChangeOrderLineUpdate,
)

logger = logging.getLogger(__name__)

SEQUENCE_PREFIX = "CO"
SEQUENCE_PADDING = 5


def _next_co_sequence(db: Session, company_id: int) -> str:
    last = (
        db.query(ChangeOrder.sequence_name)
        .filter(ChangeOrder.company_id == company_id, ChangeOrder.sequence_name.isnot(None))
        .order_by(ChangeOrder.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


class ChangeOrderService:
    """Handles Change Order CRUD, approval workflow, and line item management."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # --- Change Order CRUD ---

    def list_change_orders(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(ChangeOrder).filter(ChangeOrder.company_id == self.company_id)

        if project_id:
            query = query.filter(ChangeOrder.project_id == project_id)
        if status:
            query = query.filter(ChangeOrder.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (ChangeOrder.title.ilike(term)) | (ChangeOrder.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(ChangeOrder.id.desc()).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_change_order(self, co_id: int) -> Optional[ChangeOrder]:
        return (
            self.db.query(ChangeOrder)
            .filter(ChangeOrder.id == co_id, ChangeOrder.company_id == self.company_id)
            .first()
        )

    def get_change_order_detail(self, co_id: int) -> Optional[dict]:
        co = self.get_change_order(co_id)
        if not co:
            return None

        lines = (
            self.db.query(ChangeOrderLine)
            .filter(ChangeOrderLine.change_order_id == co_id)
            .order_by(ChangeOrderLine.id)
            .all()
        )

        line_dicts = [
            {
                "id": l.id,
                "change_order_id": l.change_order_id,
                "description": l.description,
                "quantity": l.quantity,
                "unit": l.unit,
                "unit_cost": l.unit_cost,
                "total_cost": l.total_cost,
                "company_id": l.company_id,
                "created_at": l.created_at,
                "updated_at": l.updated_at,
            }
            for l in lines
        ]

        return {
            **{c.key: getattr(co, c.key) for c in co.__table__.columns},
            "lines": line_dicts,
        }

    def create_change_order(self, data: ChangeOrderCreate) -> ChangeOrder:
        co = ChangeOrder(
            company_id=self.company_id,
            sequence_name=_next_co_sequence(self.db, self.company_id),
            title=data.title,
            description=data.description,
            reason=data.reason,
            status="draft",
            cost_impact=data.cost_impact or 0.0,
            schedule_impact_days=data.schedule_impact_days or 0,
            requested_date=data.requested_date,
            project_id=data.project_id,
            requested_by=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(co)
        self.db.flush()

        if data.lines:
            for line_data in data.lines:
                line = ChangeOrderLine(
                    change_order_id=co.id,
                    description=line_data.description,
                    quantity=line_data.quantity or 1.0,
                    unit=line_data.unit,
                    unit_cost=line_data.unit_cost or 0.0,
                    total_cost=line_data.total_cost or 0.0,
                    company_id=self.company_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(co)
        return co

    def update_change_order(self, co_id: int, data: ChangeOrderUpdate) -> Optional[ChangeOrder]:
        co = self.get_change_order(co_id)
        if not co:
            return None

        update_data = data.model_dump(exclude_unset=True)
        lines_data = update_data.pop("lines", None)

        for key, value in update_data.items():
            setattr(co, key, value)
        co.updated_by = self.user_id

        # Sync lines if provided
        if lines_data is not None:
            # Delete existing lines
            self.db.query(ChangeOrderLine).filter(
                ChangeOrderLine.change_order_id == co_id
            ).delete()

            # Create new lines
            for line_data in lines_data:
                line = ChangeOrderLine(
                    change_order_id=co_id,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1.0),
                    unit=line_data.get("unit"),
                    unit_cost=line_data.get("unit_cost", 0.0),
                    total_cost=line_data.get("total_cost", 0.0),
                    company_id=self.company_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(co)
        return co

    def delete_change_order(self, co_id: int) -> bool:
        co = self.get_change_order(co_id)
        if not co:
            return False
        self.db.delete(co)
        self.db.commit()
        return True

    def approve_change_order(self, co_id: int) -> Optional[ChangeOrder]:
        co = self.get_change_order(co_id)
        if not co:
            return None
        co.status = "approved"
        co.approved_date = date.today()
        co.approved_by = self.user_id
        co.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(co)
        return co

    def reject_change_order(self, co_id: int) -> Optional[ChangeOrder]:
        co = self.get_change_order(co_id)
        if not co:
            return None
        co.status = "rejected"
        co.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(co)
        return co

    # --- Line Item CRUD ---

    def add_line(self, co_id: int, data: ChangeOrderLineCreate) -> Optional[ChangeOrderLine]:
        co = self.get_change_order(co_id)
        if not co:
            return None

        line = ChangeOrderLine(
            change_order_id=co_id,
            description=data.description,
            quantity=data.quantity or 1.0,
            unit=data.unit,
            unit_cost=data.unit_cost or 0.0,
            total_cost=data.total_cost or 0.0,
            company_id=self.company_id,
        )
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def update_line(self, line_id: int, data: ChangeOrderLineUpdate) -> Optional[ChangeOrderLine]:
        line = (
            self.db.query(ChangeOrderLine)
            .filter(ChangeOrderLine.id == line_id, ChangeOrderLine.company_id == self.company_id)
            .first()
        )
        if not line:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(line, key, value)

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_line(self, line_id: int) -> bool:
        line = (
            self.db.query(ChangeOrderLine)
            .filter(ChangeOrderLine.id == line_id, ChangeOrderLine.company_id == self.company_id)
            .first()
        )
        if not line:
            return False
        self.db.delete(line)
        self.db.commit()
        return True
