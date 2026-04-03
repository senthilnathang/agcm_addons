"""Change Order model - construction change order with line items"""

import enum

from sqlalchemy import (
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin


class ChangeOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    VOID = "void"


class ChangeOrder(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Construction change order with approval workflow and activity logging."""

    __tablename__ = "agcm_change_orders"
    _description = "Construction change orders with line items and approval workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    status = Column(
        Enum(ChangeOrderStatus, values_callable=lambda e: [m.value for m in e]),
        default=ChangeOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )

    cost_impact = Column(Float, nullable=True, default=0.0)
    schedule_impact_days = Column(Integer, nullable=True, default=0)

    requested_date = Column(Date, nullable=True, index=True)
    approved_date = Column(Date, nullable=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requested_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")

    lines = relationship(
        "ChangeOrderLine",
        back_populates="change_order",
        cascade="all, delete-orphan",
        order_by="ChangeOrderLine.id",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_co_project_status", "project_id", "status"),
        Index("ix_agcm_co_company", "company_id"),
    )


class ChangeOrderLine(Base, TimestampMixin):
    """Line item for a change order."""

    __tablename__ = "agcm_change_order_lines"
    _description = "Change order line items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    change_order_id = Column(
        Integer,
        ForeignKey("agcm_change_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50), nullable=True)
    unit_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    change_order = relationship("ChangeOrder", back_populates="lines")

    __table_args__ = (Index("ix_agcm_col_change_order", "change_order_id"),)
