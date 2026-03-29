"""Inspection model - third-party inspection tracking"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Inspection(Base, TimestampMixin, AuditMixin):
    """
    Third-party inspection entry for a daily log.

    Migrated from Odoo 'inspection' model.
    """
    __tablename__ = "agcm_inspections"
    _description = "Third-party inspection records with type and result"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)

    # Inspection type
    inspection_type_id = Column(
        Integer,
        ForeignKey("agcm_inspection_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    result = Column(Text, nullable=False)

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
        ForeignKey("agcm_inspections.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    inspection_type = relationship("agcm_inspection_types", foreign_keys=[inspection_type_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="inspection_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_inspection_dailylog", "dailylog_id"),
    )
