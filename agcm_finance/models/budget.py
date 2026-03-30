"""Budget model - budget line items per project"""

from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class Budget(Base, TimestampMixin):
    """Budget line item for a construction project."""
    __tablename__ = "agcm_budgets"
    _description = "Budget line items with planned, actual, and committed amounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cost_code_id = Column(
        Integer,
        ForeignKey("agcm_cost_codes.id", ondelete="SET NULL"),
        nullable=True,
    )

    description = Column(String(500), nullable=False)
    planned_amount = Column(Float, default=0, nullable=False)
    actual_amount = Column(Float, default=0, nullable=False)
    committed_amount = Column(Float, default=0, nullable=False)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    cost_code = relationship("CostCode", lazy="select")

    __table_args__ = (
        Index("ix_agcm_budget_project", "project_id"),
        Index("ix_agcm_budget_company", "company_id"),
    )
