"""Drawing model - construction drawing/plan management with revisions"""

import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class DrawingStatus(str, enum.Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    VOID = "void"


class Drawing(Base, TimestampMixin, AuditMixin):
    """Construction drawing/plan linked to a project."""

    __tablename__ = "agcm_drawings"
    _description = "Construction drawings with revision tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    sheet_number = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)

    discipline = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    current_revision = Column(String(20), default="0", nullable=False)

    status = Column(
        Enum(DrawingStatus, values_callable=lambda e: [m.value for m in e]),
        default=DrawingStatus.CURRENT,
        nullable=False,
    )

    received_date = Column(Date, nullable=True)

    folder_id = Column(
        Integer,
        ForeignKey("agcm_project_folders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships — no Company/User relationships per implementation notes
    revisions = relationship(
        "DrawingRevision",
        back_populates="drawing",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_drawing_project_discipline", "project_id", "discipline"),
        Index("ix_agcm_drawing_sheet", "sheet_number"),
        Index("ix_agcm_drawing_company", "company_id"),
    )


class DrawingRevision(Base, TimestampMixin):
    """Revision record for a drawing."""

    __tablename__ = "agcm_drawing_revisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    drawing_id = Column(
        Integer,
        ForeignKey("agcm_drawings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    revision_number = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    revision_date = Column(Date, nullable=True)

    document_id = Column(
        Integer,
        ForeignKey("agcm_project_documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    file_url = Column(String(500), nullable=True)
    issued_by = Column(String(255), nullable=True)
    received_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)

    # Relationships
    drawing = relationship("Drawing", back_populates="revisions")
