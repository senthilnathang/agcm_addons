"""Project Folder model - hierarchical folder structure for document organization"""

from sqlalchemy import Column, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ProjectFolder(Base, TimestampMixin, AuditMixin):
    """Hierarchical folder structure for organizing project documents."""
    __tablename__ = "agcm_project_folders"
    _description = "Project document folders with hierarchy"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)

    parent_id = Column(
        Integer,
        ForeignKey("agcm_project_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    parent = relationship("ProjectFolder", remote_side=[id], lazy="select")
    children = relationship(
        "ProjectFolder",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
    )
    # Back-reference from parent
    parent = relationship(
        "ProjectFolder",
        remote_side=[id],
        back_populates="children",
        lazy="select",
    )
    documents = relationship(
        "ProjectDocument",
        back_populates="folder",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_folder_project", "project_id"),
        Index("ix_agcm_folder_parent", "parent_id"),
    )
