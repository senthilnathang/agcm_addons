"""Cost Code model - hierarchical cost code structure per project"""

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class CostCode(Base, TimestampMixin):
    """Hierarchical cost code for construction project budgeting."""
    __tablename__ = "agcm_cost_codes"
    _description = "Hierarchical cost codes for project budgeting"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)

    parent_id = Column(
        Integer,
        ForeignKey("agcm_cost_codes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    parent = relationship("CostCode", remote_side=[id], lazy="select")
    children = relationship(
        "CostCode",
        back_populates="parent_rel",
        lazy="select",
    )
    parent_rel = relationship(
        "CostCode",
        remote_side=[id],
        back_populates="children",
        overlaps="parent",
    )

    __table_args__ = (
        Index("ix_agcm_cc_project", "project_id"),
        Index("ix_agcm_cc_parent", "parent_id"),
        Index("ix_agcm_cc_company", "company_id"),
    )
