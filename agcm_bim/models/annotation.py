"""3D Annotation model — annotations pinned to model surfaces."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, Date
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class BIMAnnotation3D(Base, TimestampMixin, AuditMixin):
    """
    3D annotation pinned to a specific position on a BIM model surface.

    Stores world-space coordinates, camera viewpoint for recall,
    and optional links to RFIs, issues, or punch list items.
    """
    __tablename__ = "agcm_bim_annotations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)

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

    model_id = Column(
        Integer,
        ForeignKey("agcm_bim_models.id", ondelete="CASCADE"),
        nullable=True,
    )

    # 3D position on model surface
    world_pos_x = Column(Float, nullable=False, default=0)
    world_pos_y = Column(Float, nullable=False, default=0)
    world_pos_z = Column(Float, nullable=False, default=0)

    # Camera viewpoint for this annotation
    eye_x = Column(Float, nullable=True)
    eye_y = Column(Float, nullable=True)
    eye_z = Column(Float, nullable=True)
    look_x = Column(Float, nullable=True)
    look_y = Column(Float, nullable=True)
    look_z = Column(Float, nullable=True)
    up_x = Column(Float, nullable=True, default=0)
    up_y = Column(Float, nullable=True, default=1)
    up_z = Column(Float, nullable=True, default=0)

    # Entity reference
    entity_id = Column(String(255), nullable=True)  # xeokit Entity ID / IFC GlobalId

    # Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="open")  # open, in_progress, resolved

    # Assignment
    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Link to RFI or Issue
    linked_entity_type = Column(String(50), nullable=True)  # "rfi", "issue", "punch_list"
    linked_entity_id = Column(Integer, nullable=True)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    model = relationship("BIMModel", foreign_keys=[model_id], lazy="select")
    assignee = relationship("User", foreign_keys=[assigned_to], lazy="select")
