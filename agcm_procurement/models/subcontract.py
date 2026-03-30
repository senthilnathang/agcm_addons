"""Subcontract, SOV Line, and Compliance Doc models."""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class SubcontractStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETE = "complete"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SOVSourceType(str, enum.Enum):
    ORIGINAL = "original"
    CHANGE_ORDER = "change_order"


class ComplianceDocType(str, enum.Enum):
    INSURANCE_COI = "insurance_coi"
    WORKERS_COMP = "workers_comp"
    BOND = "bond"
    LICENSE = "license"
    PERMIT = "permit"
    LIEN_WAIVER = "lien_waiver"
    W9 = "w9"
    SAFETY_CERT = "safety_cert"
    OTHER = "other"


class ComplianceDocStatus(str, enum.Enum):
    REQUIRED = "required"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    EXPIRED = "expired"
    REJECTED = "rejected"


class Subcontract(Base, TimestampMixin, AuditMixin):
    """Subcontract for a construction project."""

    __tablename__ = "agcm_subcontracts"
    _description = "Subcontracts with SOV and compliance tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    contract_number = Column(String(100), nullable=True)

    vendor_name = Column(String(255), nullable=False)
    vendor_contact = Column(String(255), nullable=True)

    status = Column(
        Enum(SubcontractStatus, values_callable=lambda e: [m.value for m in e]),
        default=SubcontractStatus.DRAFT,
        nullable=False,
        index=True,
    )

    scope_of_work = Column(Text, nullable=True)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    original_amount = Column(Float, default=0, nullable=False)
    approved_cos = Column(Float, default=0, nullable=False)
    revised_amount = Column(Float, default=0, nullable=False)

    billed_to_date = Column(Float, default=0, nullable=False)
    paid_to_date = Column(Float, default=0, nullable=False)
    balance_remaining = Column(Float, default=0, nullable=False)

    retainage_pct = Column(Float, default=5.0, nullable=False)
    retainage_held = Column(Float, default=0, nullable=False)
    retainage_released = Column(Float, default=0, nullable=False)

    estimate_id = Column(
        Integer,
        ForeignKey("agcm_estimates.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    sov_lines = relationship(
        "SubcontractSOVLine",
        back_populates="subcontract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    compliance_docs = relationship(
        "SubcontractComplianceDoc",
        back_populates="subcontract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_sc_project_status", "project_id", "status"),
        Index("ix_agcm_sc_company", "company_id"),
    )


class SubcontractSOVLine(Base, TimestampMixin):
    """Schedule of Values line item (AIA G702/G703 format)."""

    __tablename__ = "agcm_subcontract_sov_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    subcontract_id = Column(
        Integer,
        ForeignKey("agcm_subcontracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    cost_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)

    scheduled_value = Column(Float, default=0, nullable=False)

    billed_previous = Column(Float, default=0, nullable=False)
    billed_current = Column(Float, default=0, nullable=False)
    stored_materials = Column(Float, default=0, nullable=False)

    total_completed = Column(Float, default=0, nullable=False)
    retainage = Column(Float, default=0, nullable=False)
    balance_to_finish = Column(Float, default=0, nullable=False)

    pct_complete = Column(Float, default=0, nullable=False)

    display_order = Column(Integer, default=0, nullable=False)

    source_type = Column(
        Enum(SOVSourceType, values_callable=lambda e: [m.value for m in e]),
        default=SOVSourceType.ORIGINAL,
        nullable=False,
    )

    # Relationships
    subcontract = relationship("Subcontract", back_populates="sov_lines")


class SubcontractComplianceDoc(Base, TimestampMixin):
    """Compliance document for a subcontract."""

    __tablename__ = "agcm_subcontract_compliance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    subcontract_id = Column(
        Integer,
        ForeignKey("agcm_subcontracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    doc_type = Column(
        Enum(ComplianceDocType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )

    status = Column(
        Enum(ComplianceDocStatus, values_callable=lambda e: [m.value for m in e]),
        default=ComplianceDocStatus.REQUIRED,
        nullable=False,
    )

    description = Column(String(255), nullable=False)

    expiration_date = Column(Date, nullable=True)

    document_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    subcontract = relationship("Subcontract", back_populates="compliance_docs")
