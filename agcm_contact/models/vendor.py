"""Vendor model — centralized vendor/client/subcontractor directory."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class VendorType(str, enum.Enum):
    VENDOR = "vendor"
    CLIENT = "client"
    SUBCONTRACTOR = "subcontractor"
    SUPPLIER = "supplier"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    CONSULTANT = "consultant"
    OTHER = "other"


class Vendor(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Centralized vendor/client/subcontractor record."""

    __tablename__ = "agcm_vendors"
    _description = "Vendor, client, and subcontractor directory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name = Column(String(255), nullable=False)
    vendor_type = Column(
        Enum(VendorType, values_callable=lambda e: [m.value for m in e]),
        default=VendorType.VENDOR.value,
        nullable=False,
    )
    code = Column(String(50), nullable=True)  # Internal vendor code

    # Primary contact
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Business info
    tax_id = Column(String(50), nullable=True)  # EIN / Tax ID
    payment_terms = Column(String(100), nullable=True)  # Net 30, Net 60, etc.
    website = Column(String(500), nullable=True)

    # Classification
    trade = Column(String(100), nullable=True)  # e.g., Electrical, Plumbing
    license_number = Column(String(100), nullable=True)
    insurance_expiry = Column(String(50), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_agcm_vendor_company", "company_id"),
        Index("ix_agcm_vendor_type", "vendor_type"),
        Index("ix_agcm_vendor_name", "company_id", "name"),
    )
