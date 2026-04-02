"""Submittal models for construction submittal management"""

import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SubmittalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    APPROVED_WITH_COMMENTS = "approved_with_comments"
    REJECTED = "rejected"
    RESUBMITTED = "resubmitted"


class SubmittalPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApproverStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_AS_NOTED = "approved_as_noted"
    REJECTED = "rejected"
    REVISE_AND_SUBMIT = "revise_and_submit"


# ---------------------------------------------------------------------------
# M2M: Submittal <-> Labels
# ---------------------------------------------------------------------------

agcm_submittal_label_rel = Table(
    "agcm_submittal_label_rel",
    Base.metadata,
    Column(
        "submittal_id",
        Integer,
        ForeignKey("agcm_submittals.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "label_id",
        Integer,
        ForeignKey("agcm_submittal_labels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ---------------------------------------------------------------------------
# Submittal Packages
# ---------------------------------------------------------------------------


class SubmittalPackage(Base, TimestampMixin):
    """Grouping container for related submittals"""

    __tablename__ = "agcm_submittal_packages"
    _description = "Submittal packages for grouping related submittals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
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

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


# ---------------------------------------------------------------------------
# Submittal Types
# ---------------------------------------------------------------------------


class SubmittalType(Base, TimestampMixin):
    """Type classification (product data, shop drawings, samples, etc.)"""

    __tablename__ = "agcm_submittal_types"
    _description = "Submittal type classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


# ---------------------------------------------------------------------------
# Submittal Labels
# ---------------------------------------------------------------------------


class SubmittalLabel(Base, TimestampMixin):
    """Color-coded labels for categorizing submittals"""

    __tablename__ = "agcm_submittal_labels"
    _description = "Submittal color-coded labels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    color = Column(String(20), nullable=False, default="#1890ff")
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


# ---------------------------------------------------------------------------
# Submittal Approvers
# ---------------------------------------------------------------------------


class SubmittalApprover(Base, TimestampMixin):
    """Multi-step approval chain entry"""

    __tablename__ = "agcm_submittal_approvers"
    _description = "Submittal approval chain entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    submittal_id = Column(
        Integer,
        ForeignKey("agcm_submittals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence = Column(Integer, nullable=False, default=1)
    status = Column(
        Enum(ApproverStatus, values_callable=lambda e: [m.value for m in e]),
        default=ApproverStatus.PENDING,
        nullable=False,
    )
    comments = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    user = relationship("User", foreign_keys=[user_id], lazy="select")


# ---------------------------------------------------------------------------
# Core Submittal
# ---------------------------------------------------------------------------


class Submittal(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Core submittal record"""

    __tablename__ = "agcm_submittals"
    _description = "Construction submittal records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers
    sequence_name = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    spec_section = Column(String(100), nullable=True)

    # Status & priority
    status = Column(
        Enum(SubmittalStatus, values_callable=lambda e: [m.value for m in e]),
        default=SubmittalStatus.DRAFT,
        nullable=False,
    )
    priority = Column(
        Enum(SubmittalPriority, values_callable=lambda e: [m.value for m in e]),
        default=SubmittalPriority.MEDIUM,
        nullable=False,
    )
    revision = Column(Integer, default=1, nullable=False)

    # Dates
    due_date = Column(Date, nullable=True)
    submitted_date = Column(Date, nullable=True)
    received_date = Column(Date, nullable=True)

    # Foreign keys
    package_id = Column(
        Integer,
        ForeignKey("agcm_submittal_packages.id", ondelete="SET NULL"),
        nullable=True,
    )
    type_id = Column(
        Integer,
        ForeignKey("agcm_submittal_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    package = relationship("SubmittalPackage", foreign_keys=[package_id], lazy="select")
    type_ = relationship("SubmittalType", foreign_keys=[type_id], lazy="select")
    submitter = relationship("User", foreign_keys=[submitted_by], lazy="select")

    labels = relationship(
        "SubmittalLabel",
        secondary=agcm_submittal_label_rel,
        lazy="select",
    )

    approvers = relationship(
        "SubmittalApprover",
        foreign_keys="SubmittalApprover.submittal_id",
        cascade="all, delete-orphan",
        order_by="SubmittalApprover.sequence",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_submittal_project_status", "project_id", "status"),
        Index("ix_agcm_submittal_company", "company_id"),
    )
