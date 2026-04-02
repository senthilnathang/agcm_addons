"""Estimation model for hierarchical cost estimation"""

import enum

from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class EstimationItem(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Hierarchical cost estimation item."""

    __tablename__ = "agcm_estimation_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cost_type = Column(
        Enum(CostType, values_callable=lambda e: [m.value for m in e]),
        default=CostType.MATERIAL,
        nullable=False,
    )
    quantity = Column(Float, default=0, nullable=False)
    unit = Column(String(50), nullable=True)
    unit_cost = Column(Float, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)
    status = Column(
        Enum(EstimationStatus, values_callable=lambda e: [m.value for m in e]),
        default=EstimationStatus.INCOMPLETE,
        nullable=False,
    )
    parent_id = Column(
        Integer,
        ForeignKey("agcm_estimation_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    children = relationship(
        "EstimationItem",
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
    )
    parent = relationship(
        "EstimationItem",
        foreign_keys=[parent_id],
        remote_side="EstimationItem.id",
        back_populates="children",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_estimation_items_project", "project_id"),
        Index("ix_agcm_estimation_items_parent", "parent_id"),
        Index("ix_agcm_estimation_items_company", "company_id"),
    )
