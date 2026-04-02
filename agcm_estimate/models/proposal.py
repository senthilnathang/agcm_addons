"""Proposal model — client-facing document generated from an estimate."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
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


class Proposal(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Client-facing proposal document generated from an estimate."""

    __tablename__ = "agcm_proposals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_name = Column(String(50), nullable=True)
    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(ProposalStatus, values_callable=lambda e: [m.value for m in e]),
        default=ProposalStatus.DRAFT,
        nullable=False,
    )
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=True)
    client_phone = Column(String(50), nullable=True)
    scope_of_work = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    payment_schedule = Column(Text, nullable=True)
    valid_until = Column(Date, nullable=True)
    sent_date = Column(Date, nullable=True)
    viewed_date = Column(DateTime, nullable=True)
    approved_date = Column(Date, nullable=True)
    show_line_items = Column(Boolean, default=True)
    show_unit_prices = Column(Boolean, default=False)
    show_markup = Column(Boolean, default=False)
    show_groups = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    version = Column(Integer, default=1)

    # Relationships
    estimate = relationship("Estimate", lazy="select")
    project = relationship("Project", lazy="select")

    __table_args__ = (
        Index("ix_agcm_proposals_project", "project_id"),
        Index("ix_agcm_proposals_estimate", "estimate_id"),
        Index("ix_agcm_proposals_status", "status"),
    )
