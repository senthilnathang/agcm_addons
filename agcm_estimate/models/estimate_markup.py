"""EstimateMarkup model for global markups (overhead, profit, contingency)."""

import enum

from sqlalchemy import (
    Boolean, Column, Enum, Float, ForeignKey, Integer, String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class MarkupType(str, enum.Enum):
    PERCENTAGE = "percentage"
    LUMP_SUM = "lump_sum"


class EstimateMarkup(Base, TimestampMixin):
    """Global markup applied to entire estimate (overhead, profit, etc.)."""

    __tablename__ = "agcm_estimate_markups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    markup_type = Column(
        Enum(MarkupType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MarkupType.PERCENTAGE,
    )
    value = Column(Float, default=0)
    apply_before_tax = Column(Boolean, default=True)
    is_compounding = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    calculated_amount = Column(Float, default=0)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    estimate = relationship("Estimate", back_populates="markups")
