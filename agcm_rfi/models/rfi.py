"""RFI model - Request for Information"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Table, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class RFIStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ANSWERED = "answered"
    CLOSED = "closed"


class RFIPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Many-to-many: RFI <-> Labels
agcm_rfi_label_rel = Table(
    "agcm_rfi_label_rel",
    Base.metadata,
    Column("rfi_id", Integer, ForeignKey("agcm_rfis.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("agcm_rfi_labels.id", ondelete="CASCADE"), primary_key=True),
)

# Many-to-many: RFI <-> Assignees
agcm_rfi_assignees = Table(
    "agcm_rfi_assignees",
    Base.metadata,
    Column("rfi_id", Integer, ForeignKey("agcm_rfis.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class RFILabel(Base, TimestampMixin):
    """Custom labels for RFI categorization."""
    __tablename__ = "agcm_rfi_labels"
    _description = "RFI custom labels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    color = Column(String(20), nullable=True, default="#1890ff")
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


class RFI(Base, TimestampMixin, AuditMixin):
    """Request for Information - core record."""
    __tablename__ = "agcm_rfis"
    _description = "Request for Information with status workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    subject = Column(String(500), nullable=False)
    question = Column(Text, nullable=True)

    priority = Column(
        Enum(RFIPriority, values_callable=lambda e: [m.value for m in e]),
        default=RFIPriority.MEDIUM,
        nullable=False,
    )

    status = Column(
        Enum(RFIStatus, values_callable=lambda e: [m.value for m in e]),
        default=RFIStatus.DRAFT,
        nullable=False,
        index=True,
    )

    schedule_impact_days = Column(Integer, nullable=True, default=0)
    cost_impact = Column(Float, nullable=True, default=0.0)

    due_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")

    labels = relationship(
        "RFILabel",
        secondary=agcm_rfi_label_rel,
        lazy="select",
    )

    assignees = relationship(
        "User",
        secondary=agcm_rfi_assignees,
        lazy="select",
    )

    responses = relationship(
        "RFIResponse",
        back_populates="rfi",
        cascade="all, delete-orphan",
        order_by="RFIResponse.created_at",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_rfi_project_status", "project_id", "status"),
        Index("ix_agcm_rfi_company", "company_id"),
    )
