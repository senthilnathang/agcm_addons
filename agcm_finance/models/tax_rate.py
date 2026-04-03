"""TaxRate model — company-level tax rate settings for invoices and bills."""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)

from app.db.base import Base
from app.models.base import TimestampMixin


class TaxRate(Base, TimestampMixin):
    """Reusable tax rate definition per company."""

    __tablename__ = "agcm_tax_rates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(100), nullable=False)  # e.g. "Sales Tax", "HST", "GST"
    rate = Column(Float, nullable=False, default=0)  # percentage, e.g. 8.25
    is_compound = Column(Boolean, default=False, nullable=False)  # stacking tax
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_agcm_tax_company", "company_id"),
    )
