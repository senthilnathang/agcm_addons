"""Photo model - photo documentation via core documents module"""

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class Photo(Base, TimestampMixin, AuditMixin):
    """
    Photo entry for a daily log.

    Images are stored via the core documents module (local/S3/etc).
    The document_id links to documents_document for the actual file.
    """
    __tablename__ = "agcm_photos"
    _description = "Construction site photos with album organisation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    album = Column(String(255), nullable=True)
    taken_on = Column(DateTime(timezone=True), nullable=True)

    # Link to core documents module for file storage
    document_id = Column(
        Integer,
        ForeignKey("documents_document.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Store the download URL for quick access
    file_url = Column(String(500), nullable=True)

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
        ForeignKey("agcm_photos.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="photo_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_photo_dailylog", "dailylog_id"),
    )
