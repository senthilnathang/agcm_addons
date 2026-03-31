"""BIM Element - extracted IFC elements for search and linking"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class BIMElement(Base):
    """
    Lightweight record of an extracted IFC element.

    Parsed from uploaded IFC models during processing.
    Stores GlobalId, type, name, material, level, and bounding box
    for search, linking to clashes, and spatial queries.
    """
    __tablename__ = "agcm_bim_elements"
    _description = "Extracted IFC elements for search and clash detection"

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

    # IFC identity
    global_id = Column(String(64), nullable=False)  # IFC GlobalId (22 char base64)
    ifc_type = Column(String(100), nullable=False)   # IfcWall, IfcDoor, IfcPipe, etc.
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Extracted properties
    properties_json = Column(Text, nullable=True)  # full IFC property sets as JSON
    material = Column(String(255), nullable=True)
    level = Column(String(100), nullable=True)      # floor/level name
    discipline = Column(String(50), nullable=True)  # architectural, structural, mep

    # Spatial
    bounding_box = Column(Text, nullable=True)  # JSON {min:{x,y,z}, max:{x,y,z}}

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    model = relationship("BIMModel", back_populates="elements", foreign_keys=[model_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_bim_element_model", "model_id"),
        Index("ix_agcm_bim_element_ifc_type", "ifc_type"),
        Index("ix_agcm_bim_element_global_id", "global_id"),
    )
