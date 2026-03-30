"""WBS model - hierarchical work breakdown structure"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class WBS(Base, TimestampMixin):
    """
    Work Breakdown Structure item.

    Hierarchical structure for organizing tasks within a schedule.
    Supports self-referential parent/children relationships.
    """
    __tablename__ = "agcm_wbs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    parent_id = Column(
        Integer,
        ForeignKey("agcm_wbs.id", ondelete="CASCADE"),
        nullable=True,
    )

    schedule_id = Column(
        Integer,
        ForeignKey("agcm_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    schedule = relationship("Schedule", foreign_keys=[schedule_id], back_populates="wbs_items")
    parent = relationship("WBS", remote_side=[id], back_populates="children", lazy="select")
    children = relationship("WBS", back_populates="parent", cascade="all, delete-orphan", lazy="select")

    __table_args__ = (
        Index("ix_agcm_wbs_schedule", "schedule_id"),
    )
