"""Safety Violation/Observation model"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class SafetyViolation(Base, TimestampMixin, AuditMixin):
    """
    Safety observation/violation entry for a daily log.

    Migrated from Odoo 'safety.violation' model.
    """
    __tablename__ = "agcm_safety_violations"
    _description = "Safety observation and violation notices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)  # Description

    # Created by user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Notice to (contractor/partner)
    partner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    violation_notice = Column(Text, nullable=False)

    # Violation type
    violation_type_id = Column(
        Integer,
        ForeignKey("agcm_violation_types.id", ondelete="SET NULL"),
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
        ForeignKey("agcm_safety_violations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    reporter = relationship("User", foreign_keys=[user_id], lazy="select")
    notice_to = relationship("User", foreign_keys=[partner_id], lazy="select")
    violation_type = relationship("agcm_violation_types", foreign_keys=[violation_type_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="safety_violation_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_safety_violation_dailylog", "dailylog_id"),
    )
