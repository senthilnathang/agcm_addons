"""Vendor Bill, Vendor Bill Line, and Vendor Bill Payment models.

This is the enhanced vendor bill model with line items, payments, OCR, and PO matching.
Separate from the simple agcm_finance.Bill model.
"""

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


class BillRecordType(str, enum.Enum):
    BILL = "bill"
    CREDIT_MEMO = "credit_memo"
    DEBIT_MEMO = "debit_memo"


class VendorBillStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"


class BillLineType(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    OTHER = "other"


class VendorBill(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Enhanced vendor bill with line items, payments, OCR, and PO matching."""

    __tablename__ = "agcm_vendor_bills"
    _description = "Vendor bills with line items, payments, and duplicate detection"

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
    bill_number = Column(String(100), nullable=True)

    vendor_name = Column(String(255), nullable=False)
    vendor_contact = Column(String(255), nullable=True)

    record_type = Column(
        Enum(BillRecordType, values_callable=lambda e: [m.value for m in e]),
        default=BillRecordType.BILL,
        nullable=False,
    )

    status = Column(
        Enum(VendorBillStatus, values_callable=lambda e: [m.value for m in e]),
        default=VendorBillStatus.DRAFT,
        nullable=False,
        index=True,
    )

    bill_reference = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    issue_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    subtotal = Column(Float, default=0, nullable=False)
    tax_amount = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)

    paid_amount = Column(Float, default=0, nullable=False)
    balance_due = Column(Float, default=0, nullable=False)

    payment_terms = Column(String(100), nullable=True)

    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_date = Column(Date, nullable=True)

    purchase_order_id = Column(
        Integer,
        ForeignKey("agcm_purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    subcontract_id = Column(
        Integer,
        ForeignKey("agcm_subcontracts.id", ondelete="SET NULL"),
        nullable=True,
    )

    ocr_processed = Column(Boolean, default=False, nullable=False)
    ocr_confidence = Column(Float, nullable=True)

    original_file_url = Column(String(500), nullable=True)

    vendor_invoice_ref = Column(String(255), nullable=True)
    duplicate_flag = Column(Boolean, default=False, nullable=False)

    duplicate_of_id = Column(
        Integer,
        ForeignKey("agcm_vendor_bills.id", ondelete="SET NULL"),
        nullable=True,
    )

    notes = Column(Text, nullable=True)

    # Relationships
    lines = relationship(
        "VendorBillLine",
        back_populates="bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    payments = relationship(
        "VendorBillPayment",
        back_populates="bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_vb_project_status", "project_id", "status"),
        Index("ix_agcm_vb_company", "company_id"),
        Index("ix_agcm_vb_vendor_invoice_ref", "vendor_invoice_ref"),
    )


class VendorBillLine(Base, TimestampMixin):
    """Line item on a vendor bill."""

    __tablename__ = "agcm_vendor_bill_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    bill_id = Column(
        Integer,
        ForeignKey("agcm_vendor_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    cost_code = Column(String(50), nullable=True)

    po_line_id = Column(
        Integer,
        ForeignKey("agcm_purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    line_type = Column(
        Enum(BillLineType, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )

    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=0, nullable=False)
    unit = Column(String(50), default="ea", nullable=False)
    unit_cost = Column(Float, default=0, nullable=False)
    amount = Column(Float, default=0, nullable=False)

    display_order = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    bill = relationship("VendorBill", back_populates="lines")


class VendorBillPayment(Base, TimestampMixin):
    """Payment record for a vendor bill."""

    __tablename__ = "agcm_vendor_bill_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    bill_id = Column(
        Integer,
        ForeignKey("agcm_vendor_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)

    payment_method = Column(String(50), nullable=False)
    reference_number = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)

    recorded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    bill = relationship("VendorBill", back_populates="payments")
