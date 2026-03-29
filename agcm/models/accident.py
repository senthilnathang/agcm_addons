"""Accident model - incident reporting"""

from sqlalchemy import (
    Column, Boolean, DateTime, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Accident(Base, TimestampMixin, AuditMixin):
    """
    Accident/incident entry for a daily log.

    Migrated from Odoo 'accident' model.
    """
    __tablename__ = "agcm_accidents"
    _description = "Accident and incident reports with resolution tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(Text, nullable=False)  # Description

    # Accident type
    accident_type_id = Column(
        Integer,
        ForeignKey("agcm_accident_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    resolution = Column(String(500), nullable=True)
    incident_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String(255), nullable=True)
    safety_measure_precautions = Column(Boolean, default=False, nullable=True)

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
        ForeignKey("agcm_accidents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    accident_type = relationship("agcm_accident_types", foreign_keys=[accident_type_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="accident_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_accident_dailylog", "dailylog_id"),
    )
