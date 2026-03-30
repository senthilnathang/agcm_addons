"""Project Image model for progress photos"""

from sqlalchemy import (
    Column, Date, ForeignKey, Index, Integer, String, Text,
)

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ProjectImage(Base, TimestampMixin, AuditMixin):
    """Progress photo with metadata."""

    __tablename__ = "agcm_project_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    document_id = Column(Integer, nullable=True)
    file_url = Column(String(1000), nullable=True)
    file_name = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    taken_on = Column(Date, nullable=True)
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agcm_project_images_project", "project_id"),
        Index("ix_agcm_project_images_company", "company_id"),
    )
