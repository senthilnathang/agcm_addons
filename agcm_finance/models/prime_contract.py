"""Prime Contract model - Owner-to-GC contract"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Text, Index,
)

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class PrimeContractStatus(str, enum.Enum):
    DRAFT = "draft"
    EXECUTED = "executed"
    ACTIVE = "active"
    COMPLETE = "complete"
    CLOSED = "closed"


class PrimeContract(Base, TimestampMixin, AuditMixin):
    """Owner-to-GC prime contract."""

    __tablename__ = "agcm_prime_contracts"
    _description = "Prime contracts between owner and general contractor"

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
    contract_number = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    owner_name = Column(String(255), nullable=False)

    status = Column(
        Enum(PrimeContractStatus, values_callable=lambda e: [m.value for m in e]),
        default=PrimeContractStatus.DRAFT,
        nullable=False,
    )

    original_value = Column(Float, default=0, nullable=False)
    approved_changes = Column(Float, default=0, nullable=False)
    revised_value = Column(Float, default=0, nullable=False)
    billed_to_date = Column(Float, default=0, nullable=False)
    paid_to_date = Column(Float, default=0, nullable=False)
    retainage_held = Column(Float, default=0, nullable=False)
    retainage_pct = Column(Float, default=0, nullable=False)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    executed_date = Column(Date, nullable=True)

    contract_type = Column(String(50), default="lump_sum", nullable=False)
    payment_terms = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_agcm_pc_project", "project_id"),
        Index("ix_agcm_pc_company", "company_id"),
    )
