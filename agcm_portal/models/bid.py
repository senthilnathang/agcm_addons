"""Bid models - bid packages and submissions from subcontractors"""

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
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class BidStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class BidPackage(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Bid request sent to subcontractors."""

    __tablename__ = "agcm_bid_packages"
    __table_args__ = {"extend_existing": True}

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
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trade = Column(String(100), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="open", nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    submissions = relationship(
        "BidSubmission",
        back_populates="bid_package",
        cascade="all, delete-orphan",
    )


class BidSubmission(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Subcontractor response to a bid package."""

    __tablename__ = "agcm_bid_submissions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    bid_package_id = Column(
        Integer,
        ForeignKey("agcm_bid_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vendor_name = Column(String(255), nullable=False)
    vendor_email = Column(String(255), nullable=True)
    vendor_phone = Column(String(50), nullable=True)

    status = Column(
        Enum(
            BidStatus,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=BidStatus.DRAFT,
        nullable=False,
    )

    total_amount = Column(Float, default=0)
    scope_description = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    submitted_date = Column(Date, nullable=True)
    document_url = Column(String(500), nullable=True)
    is_awarded = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Relationships
    bid_package = relationship("BidPackage", back_populates="submissions")
