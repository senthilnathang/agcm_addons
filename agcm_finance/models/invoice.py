"""Invoice model - customer invoices for construction projects"""

import enum

from sqlalchemy import (
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class Invoice(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Customer invoice for a construction project."""

    __tablename__ = "agcm_invoices"
    _description = "Customer invoices with payment tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    client_name = Column(String(255), nullable=False)

    status = Column(
        Enum(InvoiceStatus, values_callable=lambda e: [m.value for m in e]),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )

    amount = Column(Float, default=0, nullable=False)
    tax_amount = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)
    balance_due = Column(Float, default=0, nullable=False)

    issue_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_inv_project_status", "project_id", "status"),
        Index("ix_agcm_inv_company", "company_id"),
    )
