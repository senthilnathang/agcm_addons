"""Purchase Order and Purchase Order Line models."""

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


class PurchaseOrder(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Purchase order for a construction project."""

    __tablename__ = "agcm_purchase_orders"
    _description = "Purchase orders with line items and delivery tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    po_number = Column(String(100), nullable=True)

    vendor_name = Column(String(255), nullable=False)
    vendor_contact = Column(String(255), nullable=True)

    status = Column(
        Enum(PurchaseOrderStatus, values_callable=lambda e: [m.value for m in e]),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )

    description = Column(Text, nullable=True)

    issue_date = Column(Date, nullable=True)
    expected_delivery = Column(Date, nullable=True)
    actual_delivery = Column(Date, nullable=True)

    shipping_method = Column(String(100), nullable=True)
    shipping_address = Column(Text, nullable=True)

    subtotal = Column(Float, default=0, nullable=False)
    tax_amount = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)

    retainage_pct = Column(Float, default=0, nullable=False)
    retainage_amount = Column(Float, default=0, nullable=False)

    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_po_project_status", "project_id", "status"),
        Index("ix_agcm_po_company", "company_id"),
    )


class PurchaseOrderLine(Base, TimestampMixin):
    """Line item on a purchase order."""

    __tablename__ = "agcm_purchase_order_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    po_id = Column(
        Integer,
        ForeignKey("agcm_purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    cost_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)

    item_type = Column(
        Enum(ItemType, values_callable=lambda e: [m.value for m in e]),
        default=ItemType.MATERIAL,
        nullable=False,
    )

    quantity = Column(Float, default=0, nullable=False)
    unit = Column(String(50), default="ea", nullable=False)
    unit_cost = Column(Float, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)

    received_qty = Column(Float, default=0, nullable=False)

    display_order = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (Index("ix_agcm_po_line_po", "po_id"),)
