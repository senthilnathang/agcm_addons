"""Bill model - vendor bills for construction projects"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class BillStatus(str, enum.Enum):
    DRAFT = "draft"
    RECEIVED = "received"
    APPROVED = "approved"
    PAID = "paid"
    OVERDUE = "overdue"


class Bill(Base, TimestampMixin, AuditMixin):
    """Vendor bill for a construction project."""
    __tablename__ = "agcm_bills"
    _description = "Vendor bills with payment tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    bill_number = Column(String(100), nullable=True)
    vendor_name = Column(String(255), nullable=False)

    status = Column(
        Enum(BillStatus, values_callable=lambda e: [m.value for m in e]),
        default=BillStatus.DRAFT,
        nullable=False,
        index=True,
    )

    amount = Column(Float, default=0, nullable=False)
    tax_amount = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)

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
        Index("ix_agcm_bill_project_status", "project_id", "status"),
        Index("ix_agcm_bill_company", "company_id"),
    )
