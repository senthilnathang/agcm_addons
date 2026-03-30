"""Assembly models for reusable grouped cost templates."""

import enum

from sqlalchemy import (
    Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ItemType(str, enum.Enum):
    """Item type for assembly items (mirrors cost_catalog.ItemType)."""
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    FEE = "fee"
    OTHER = "other"


class Assembly(Base, TimestampMixin, AuditMixin):
    """Reusable grouped cost template (e.g. 'Interior Wall Assembly')."""

    __tablename__ = "agcm_assemblies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    items = relationship(
        "AssemblyItem",
        back_populates="assembly",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AssemblyItem(Base, TimestampMixin):
    """Individual item within an assembly template."""

    __tablename__ = "agcm_assembly_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assembly_id = Column(
        Integer,
        ForeignKey("agcm_assemblies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_item_id = Column(
        Integer,
        ForeignKey("agcm_cost_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(
        Enum(ItemType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ItemType.MATERIAL,
    )
    quantity = Column(Float, default=1)
    unit = Column(String(50), default="ea")
    unit_cost = Column(Float, default=0)
    waste_factor = Column(Float, default=0)  # percentage
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    assembly = relationship("Assembly", back_populates="items")
    cost_item = relationship("CostItem", lazy="select")
