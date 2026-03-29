"""Delay model - delay tracking"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Delay(Base, TimestampMixin, AuditMixin):
    """
    Delay entry for a daily log.

    Migrated from Odoo 'delay' model.
    Tracks delays with reason, contractor, and reporter.
    """
    __tablename__ = "agcm_delays"
    _description = "Construction delay records with reason and contractor"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    reason = Column(String(500), nullable=False)
    delay = Column(Text, nullable=True)  # Delay description
    reported_by = Column(String(255), nullable=True)

    # Contractor
    partner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
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
        ForeignKey("agcm_delays.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    contractor = relationship("User", foreign_keys=[partner_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="delay_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_delay_dailylog", "dailylog_id"),
    )
