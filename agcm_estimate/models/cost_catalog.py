"""Cost Catalog and Cost Item models for reusable cost libraries."""

import enum

from sqlalchemy import (
    Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ItemType(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    FEE = "fee"
    OTHER = "other"


class CostCatalog(Base, TimestampMixin, AuditMixin):
    """Company-wide reusable cost catalog."""

    __tablename__ = "agcm_cost_catalogs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)

    # Relationships
    items = relationship(
        "CostItem",
        back_populates="catalog",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class CostItem(Base, TimestampMixin):
    """Individual cost item within a catalog."""

    __tablename__ = "agcm_cost_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_id = Column(
        Integer,
        ForeignKey("agcm_cost_catalogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(
        Enum(ItemType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ItemType.MATERIAL,
    )
    unit = Column(String(50), default="ea")
    unit_cost = Column(Float, default=0)
    unit_price = Column(Float, default=0)
    taxable = Column(Boolean, default=True)
    cost_code = Column(String(50), nullable=True)
    vendor = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    catalog = relationship("CostCatalog", back_populates="items")

    __table_args__ = (
        Index("ix_agcm_cost_items_catalog_type", "catalog_id", "item_type"),
    )
