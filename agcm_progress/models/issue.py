"""Issue model for project issue tracking"""

import enum

from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IssuePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Issue(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Project issue with severity, status, and priority workflow."""

    __tablename__ = "agcm_issues"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_name = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(
        Enum(IssueSeverity, values_callable=lambda e: [m.value for m in e]),
        default=IssueSeverity.MINOR,
        nullable=False,
    )
    status = Column(
        Enum(IssueStatus, values_callable=lambda e: [m.value for m in e]),
        default=IssueStatus.OPEN,
        nullable=False,
    )
    priority = Column(
        Enum(IssuePriority, values_callable=lambda e: [m.value for m in e]),
        default=IssuePriority.MEDIUM,
        nullable=False,
    )
    location = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)
    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reported_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    project = relationship("Project", foreign_keys=[project_id], lazy="select")
    assigned_user = relationship("User", foreign_keys=[assigned_to], lazy="select")
    reporter = relationship("User", foreign_keys=[reported_by], lazy="select")

    __table_args__ = (
        Index("ix_agcm_issues_project_status", "project_id", "status"),
        Index("ix_agcm_issues_company", "company_id"),
        Index("ix_agcm_issues_severity", "severity"),
    )
