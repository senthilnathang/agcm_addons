"""Payment Application model - AIA G702/G703 progress billing"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class PaymentApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CERTIFIED = "certified"
    PAID = "paid"
    REJECTED = "rejected"


class PaymentApplication(Base, TimestampMixin, AuditMixin):
    """Progress billing per period (AIA G702/G703)."""

    __tablename__ = "agcm_payment_applications"
    _description = "Payment applications for progress billing"

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
    application_number = Column(Integer, nullable=False)

    subcontract_id = Column(
        Integer,
        ForeignKey("agcm_subcontracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_from = Column(Date, nullable=False)
    period_to = Column(Date, nullable=False)

    status = Column(
        Enum(PaymentApplicationStatus, values_callable=lambda e: [m.value for m in e]),
        default=PaymentApplicationStatus.DRAFT,
        nullable=False,
    )

    scheduled_value = Column(Float, default=0, nullable=False)
    previous_billed = Column(Float, default=0, nullable=False)
    current_billed = Column(Float, default=0, nullable=False)
    stored_materials = Column(Float, default=0, nullable=False)
    total_completed = Column(Float, default=0, nullable=False)
    retainage_held = Column(Float, default=0, nullable=False)
    retainage_released = Column(Float, default=0, nullable=False)
    net_payment_due = Column(Float, default=0, nullable=False)
    pct_complete = Column(Float, default=0, nullable=False)

    certified_by = Column(String(255), nullable=True)
    certified_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    lines = relationship(
        "PaymentApplicationLine",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_pa_subcontract", "subcontract_id"),
        Index("ix_agcm_pa_project", "project_id"),
        Index("ix_agcm_pa_company", "company_id"),
    )


class PaymentApplicationLine(Base, TimestampMixin):
    """Line item for a payment application."""

    __tablename__ = "agcm_payment_application_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    application_id = Column(
        Integer,
        ForeignKey("agcm_payment_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    sov_line_id = Column(
        Integer,
        ForeignKey("agcm_subcontract_sov_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    description = Column(String(500), nullable=False)
    scheduled_value = Column(Float, default=0, nullable=False)
    previous_billed = Column(Float, default=0, nullable=False)
    current_billed = Column(Float, default=0, nullable=False)
    stored_materials = Column(Float, default=0, nullable=False)
    total_completed = Column(Float, default=0, nullable=False)
    retainage = Column(Float, default=0, nullable=False)
    balance_to_finish = Column(Float, default=0, nullable=False)
    pct_complete = Column(Float, default=0, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    application = relationship("PaymentApplication", back_populates="lines")
