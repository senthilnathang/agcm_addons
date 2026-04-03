"""Estimate, EstimateGroup, and EstimateLineItem models."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
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
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin


class EstimateStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EstimateType(str, enum.Enum):
    PRELIMINARY = "preliminary"
    SCHEMATIC = "schematic"
    DETAILED = "detailed"
    STIPULATED_SUM = "stipulated_sum"
    COST_PLUS = "cost_plus"
    UNIT_PRICE = "unit_price"
    DESIGN_BUILD = "design_build"


class LineItemType(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    OTHER = "other"


class Estimate(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Top-level estimate for a construction project."""

    __tablename__ = "agcm_estimates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_name = Column(String(50), nullable=True)
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    status = Column(
        Enum(EstimateStatus, values_callable=lambda e: [m.value for m in e]),
        default=EstimateStatus.DRAFT,
        nullable=False,
    )
    estimate_type = Column(
        Enum(EstimateType, values_callable=lambda e: [m.value for m in e]),
        default=EstimateType.DETAILED,
        nullable=False,
    )
    subtotal = Column(Float, default=0)
    markup_total = Column(Float, default=0)
    tax_total = Column(Float, default=0)
    grand_total = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date = Column(Date, nullable=True)
    parent_estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    groups = relationship(
        "EstimateGroup",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="EstimateGroup.display_order",
        lazy="selectin",
    )
    markups = relationship(
        "EstimateMarkup",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="EstimateMarkup.display_order",
        lazy="selectin",
    )
    parent_estimate = relationship("Estimate", remote_side=[id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_estimates_project_status", "project_id", "status"),
        Index("ix_agcm_estimates_company", "company_id"),
    )


class EstimateGroup(Base, TimestampMixin):
    """Section/group within an estimate (e.g. 'Foundation', 'Framing')."""

    __tablename__ = "agcm_estimate_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    subtotal = Column(Float, default=0)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    estimate = relationship("Estimate", back_populates="groups")
    line_items = relationship(
        "EstimateLineItem",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="EstimateLineItem.display_order",
        lazy="selectin",
    )


class EstimateLineItem(Base, TimestampMixin):
    """Individual cost line within an estimate group."""

    __tablename__ = "agcm_estimate_line_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(
        Integer,
        ForeignKey("agcm_estimate_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="CASCADE"),
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
        Enum(LineItemType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=LineItemType.MATERIAL,
    )
    quantity = Column(Float, default=0)
    unit = Column(String(50), default="ea")
    unit_cost = Column(Float, default=0)
    unit_price = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    total_price = Column(Float, default=0)
    markup_pct = Column(Float, default=0)
    taxable = Column(Boolean, default=True)
    cost_code = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    group = relationship("EstimateGroup", back_populates="line_items")
    cost_item = relationship("CostItem", lazy="select")

    __table_args__ = (
        Index("ix_agcm_estimate_line_items_estimate", "estimate_id"),
        Index("ix_agcm_estimate_line_items_group", "group_id"),
    )
