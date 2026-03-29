"""Visitor model - visitor log tracking"""

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Visitor(Base, TimestampMixin, AuditMixin):
    """
    Visitor entry for a daily log.

    Migrated from Odoo 'visitor' model.
    Tracks who visited the site, why, and when.
    """
    __tablename__ = "agcm_visitors"
    _description = "Site visitor log entries with entry/exit tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)  # Visitor Name
    reason = Column(Text, nullable=False)  # Visit Reason

    # Visit times
    visit_entry_time = Column(DateTime(timezone=True), nullable=False)
    visit_exit_time = Column(DateTime(timezone=True), nullable=True)

    comments = Column(String(500), nullable=True)

    # Person to meet
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Daily log link
    dailylog_id = Column(
        Integer,
        ForeignKey("agcm_daily_activity_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project link
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Copy tracking
    copy_id = Column(
        Integer,
        ForeignKey("agcm_visitors.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    person_to_meet = relationship("User", foreign_keys=[user_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="visitor_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_visitor_dailylog", "dailylog_id"),
    )
