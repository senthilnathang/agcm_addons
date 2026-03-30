"""Milestone model for project progress tracking"""

from sqlalchemy import (
    Boolean, Column, Date, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Milestone(Base, TimestampMixin, AuditMixin):
    """Project milestone with planned and actual dates."""

    __tablename__ = "agcm_milestones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    project = relationship("Project", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_milestones_project", "project_id"),
        Index("ix_agcm_milestones_company", "company_id"),
    )
