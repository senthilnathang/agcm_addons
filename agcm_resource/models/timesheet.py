"""Timesheet model - daily time entries for construction workers"""

import enum

from sqlalchemy import (
    Column, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class TimesheetStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Timesheet(Base, TimestampMixin, AuditMixin):
    """
    Daily timesheet entry for a construction worker.

    Tracks hours worked, costs, and approval workflow.
    """
    __tablename__ = "agcm_timesheets"
    _description = "Construction worker timesheets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Sequence
    sequence_name = Column(String(50), nullable=True)

    # References
    worker_id = Column(
        Integer,
        ForeignKey("agcm_workers.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Date & time
    date = Column(Date, nullable=False)
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)

    # Hours
    regular_hours = Column(Float, default=0, nullable=False)
    overtime_hours = Column(Float, default=0, nullable=False)
    double_time_hours = Column(Float, default=0, nullable=False)
    total_hours = Column(Float, default=0, nullable=False)

    # Costs
    regular_cost = Column(Float, default=0, nullable=False)
    overtime_cost = Column(Float, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)

    # Status & approval
    status = Column(
        Enum(TimesheetStatus, values_callable=lambda e: [m.value for m in e]),
        default=TimesheetStatus.DRAFT,
        nullable=False,
    )
    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date = Column(Date, nullable=True)

    # Details
    task_description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    worker = relationship("agcm_workers", foreign_keys=[worker_id], lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_timesheets_worker_date", "worker_id", "date"),
        Index("ix_agcm_timesheets_project_date", "project_id", "date"),
        Index("ix_agcm_timesheets_company", "company_id"),
    )
