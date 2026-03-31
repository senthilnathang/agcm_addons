"""BIM Viewpoint - saved camera positions, section planes, and annotations"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class BIMViewpoint(Base, TimestampMixin):
    """
    Saved camera position / annotation on a BIM model.

    Follows BCF (BIM Collaboration Format) viewpoint conventions.
    Can be linked to other entities like RFIs, issues, or clash results
    via entity_type + entity_id polymorphic link.
    """
    __tablename__ = "agcm_bim_viewpoints"
    _description = "BCF-style viewpoints with camera, sections, and annotations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_id = Column(
        Integer,
        ForeignKey("agcm_bim_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Camera state (JSON)
    camera_position = Column(Text, nullable=True)  # {x, y, z, rx, ry, rz, fov}
    camera_target = Column(Text, nullable=True)     # {x, y, z}

    # Section planes (JSON array)
    section_planes = Column(Text, nullable=True)    # [{pos:{x,y,z}, dir:{x,y,z}}]

    # Visibility (JSON arrays of element GlobalIds)
    visible_elements = Column(Text, nullable=True)
    hidden_elements = Column(Text, nullable=True)

    # Markup annotations (JSON array)
    annotations = Column(Text, nullable=True)       # [{type, x, y, text, color}]

    # Full BCF 2.1 JSON (replaces simple camera_position for full viewpoint persistence)
    bcf_data = Column(Text, nullable=True)

    # Thumbnail / snapshot
    screenshot_url = Column(String(500), nullable=True)
    snapshot_url = Column(String(500), nullable=True)      # PNG screenshot file path
    snapshot_base64 = Column(Text, nullable=True)           # base64-encoded screenshot for quick display

    # Polymorphic entity link
    entity_type = Column(String(100), nullable=True)  # "rfi", "issue", "clash", "submittal"
    entity_id = Column(Integer, nullable=True)

    # Direct entity FK links (convenience, in addition to polymorphic)
    linked_rfi_id = Column(Integer, nullable=True)
    linked_issue_id = Column(Integer, nullable=True)

    # Tags for filtering (comma-separated)
    tags = Column(String(500), nullable=True)

    # Creator
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    model = relationship("BIMModel", back_populates="viewpoints", foreign_keys=[model_id], lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")

    __table_args__ = (
        Index("ix_agcm_bim_viewpoint_model", "model_id"),
        Index("ix_agcm_bim_viewpoint_entity", "entity_type", "entity_id"),
    )
