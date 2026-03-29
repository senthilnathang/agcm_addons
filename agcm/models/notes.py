"""Notes/Observations model"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Notes(Base, TimestampMixin, AuditMixin):
    """
    Observation/notes entry for a daily log.

    Migrated from Odoo 'notes' model.
    """
    __tablename__ = "agcm_notes"
    _description = "Daily activity observations and notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)  # Comments
    note = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    issue = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)

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
        ForeignKey("agcm_notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="notes_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_notes_dailylog", "dailylog_id"),
    )
