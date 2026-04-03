"""BIM Model - uploaded 3D model files with versioning"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class BIMModelStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class BIMModel(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """
    Uploaded 3D model file.

    Supports IFC, RVT, NWD, FBX, glTF/GLB, and OBJ formats.
    Models can be versioned via parent_model_id chain.
    Metadata is extracted during processing (element count, units, geo, author).
    """

    __tablename__ = "agcm_bim_models"
    _description = "BIM 3D model files with versioning and metadata extraction"

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

    # Identifiers
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Classification
    discipline = Column(
        String(50), nullable=True
    )  # architectural, structural, mep, civil, composite

    # File info
    file_format = Column(String(20), nullable=True)  # ifc, rvt, nwd, fbx, glb, obj
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes

    # Converted XKT file (for xeokit viewer)
    xkt_file_url = Column(String(500), nullable=True)  # path to converted .xkt
    file_size_xkt = Column(Integer, nullable=True)  # XKT file size in bytes

    # Federation transforms (for multi-model positioning)
    position_x = Column(Float, default=0, nullable=True)
    position_y = Column(Float, default=0, nullable=True)
    position_z = Column(Float, default=0, nullable=True)
    rotation_x = Column(Float, default=0, nullable=True)
    rotation_y = Column(Float, default=0, nullable=True)
    rotation_z = Column(Float, default=0, nullable=True)
    scale_factor = Column(Float, default=1.0, nullable=True)

    # Processing
    status = Column(
        Enum(BIMModelStatus, values_callable=lambda e: [m.value for m in e]),
        default=BIMModelStatus.UPLOADING,
        nullable=False,
        index=True,
    )

    # Versioning
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    parent_model_id = Column(
        Integer,
        ForeignKey("agcm_bim_models.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Extracted metadata
    metadata_json = Column(
        Text, nullable=True
    )  # JSON: units, geo, author, application, schema
    element_count = Column(Integer, default=0, nullable=False)
    processing_error = Column(Text, nullable=True)

    # Uploader
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    uploader = relationship("User", foreign_keys=[uploaded_by], lazy="select")
    parent_model = relationship(
        "BIMModel", remote_side=[id], foreign_keys=[parent_model_id], lazy="select"
    )

    viewpoints = relationship(
        "BIMViewpoint",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="select",
    )

    elements = relationship(
        "BIMElement",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("ix_agcm_bim_model_project_discipline", "project_id", "discipline"),
        Index("ix_agcm_bim_model_company", "company_id"),
        {"extend_existing": True},
    )
