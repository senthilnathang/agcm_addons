"""Schedule model - versioned project schedules"""

import enum

from sqlalchemy import (
    Boolean, Column, Enum, ForeignKey, Integer, String,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ScheduleType(str, enum.Enum):
    BASELINE = "baseline"
    REVISED = "revised"
    CURRENT = "current"


class Schedule(Base, TimestampMixin, AuditMixin):
    """
    Schedule version for a construction project.

    Each project can have multiple schedule versions (baseline, revised, current).
    Only one schedule per project can be active at a time.
    """
    __tablename__ = "agcm_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    version = Column(Integer, default=1, nullable=False)

    schedule_type = Column(
        Enum(ScheduleType, values_callable=lambda e: [m.value for m in e]),
        default=ScheduleType.BASELINE,
        nullable=False,
    )
    is_active = Column(Boolean, default=False, nullable=False)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id], lazy="select")
    wbs_items = relationship(
        "WBS",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    tasks = relationship(
        "Task",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agcm_schedules_project", "project_id"),
        Index("ix_agcm_schedules_company", "company_id"),
    )
