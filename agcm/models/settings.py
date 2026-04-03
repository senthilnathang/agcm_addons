"""AGCMSettings model — per-module company-level configuration."""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class AGCMSettings(Base, TimestampMixin, AuditMixin):
    """Company-level settings per AGCM module."""

    __tablename__ = "agcm_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    module_name = Column(String(100), nullable=False)  # finance, procurement, estimate, etc.

    # Common construction settings
    default_retention_pct = Column(Float, default=10.0, nullable=False)
    default_markup_pct = Column(Float, default=0, nullable=False)
    default_tax_rate_pct = Column(Float, default=0, nullable=False)
    default_payment_terms = Column(String(100), default="Net 30", nullable=False)
    po_number_prefix = Column(String(20), default="PO", nullable=False)
    invoice_number_prefix = Column(String(20), default="INV", nullable=False)
    currency_code = Column(String(10), default="USD", nullable=False)
    working_hours_per_day = Column(Float, default=8.0, nullable=False)
    overtime_multiplier = Column(Float, default=1.5, nullable=False)

    # Module-specific extensible settings (JSONB for flexibility)
    settings_json = Column(JSONB, default={}, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "module_name", name="uq_agcm_settings_company_module"),
        Index("ix_agcm_settings_company", "company_id"),
    )
