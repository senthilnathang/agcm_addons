"""Project Document model - documents linked to folders"""

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class DocumentType(str, enum.Enum):
    BLUEPRINT = "blueprint"
    CONTRACT = "contract"
    PERMIT = "permit"
    INVOICE = "invoice"
    INSPECTION_REPORT = "inspection_report"
    CHANGE_ORDER = "change_order"
    SPECIFICATION = "specification"
    SCHEDULE = "schedule"
    SAFETY_REPORT = "safety_report"
    MATERIAL_LIST = "material_list"
    SUBMITTAL = "submittal"
    RFI = "rfi"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProjectDocument(Base, TimestampMixin, AuditMixin):
    """Project document with type, status, and folder organization."""
    __tablename__ = "agcm_project_documents"
    _description = "Project documents with folder organization and status workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    document_type = Column(
        Enum(DocumentType, values_callable=lambda e: [m.value for m in e]),
        default=DocumentType.OTHER,
        nullable=False,
    )

    status = Column(
        Enum(DocumentStatus, values_callable=lambda e: [m.value for m in e]),
        default=DocumentStatus.DRAFT,
        nullable=False,
    )

    revision = Column(Integer, default=1, nullable=False)

    # File reference (via core documents module or direct URL)
    document_id = Column(Integer, nullable=True)
    file_name = Column(String(500), nullable=True)
    file_url = Column(String(1000), nullable=True)

    # Relations
    folder_id = Column(
        Integer,
        ForeignKey("agcm_project_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    folder = relationship("ProjectFolder", back_populates="documents", lazy="select")

    __table_args__ = (
        Index("ix_agcm_doc_project_folder", "project_id", "folder_id"),
        Index("ix_agcm_doc_project_type", "project_id", "document_type"),
        Index("ix_agcm_doc_company", "company_id"),
    )
