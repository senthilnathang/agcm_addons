"""BillLine model — itemized line items for vendor bills."""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class BillLine(Base, TimestampMixin):
    """Line item on a vendor bill."""

    __tablename__ = "agcm_bill_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    bill_id = Column(
        Integer,
        ForeignKey("agcm_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit = Column(String(50), default="ea", nullable=True)
    unit_cost = Column(Float, default=0, nullable=False)

    subtotal = Column(Float, default=0, nullable=False)  # qty × unit_cost

    taxable = Column(Boolean, default=True, nullable=False)
    tax_rate_id = Column(
        Integer,
        ForeignKey("agcm_tax_rates.id", ondelete="SET NULL"),
        nullable=True,
    )
    tax_amount = Column(Float, default=0, nullable=False)
    total = Column(Float, default=0, nullable=False)  # subtotal + tax_amount

    cost_code_id = Column(
        Integer,
        ForeignKey("agcm_cost_codes.id", ondelete="SET NULL"),
        nullable=True,
    )

    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    bill = relationship("Bill", back_populates="lines")

    __table_args__ = (
        Index("ix_agcm_bll_bill", "bill_id"),
    )
