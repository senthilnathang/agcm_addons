"""Punch list model - deficiency tracking with assignment workflow"""

import enum

from sqlalchemy import (
    Column, Date, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class PunchItemStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"


class PunchItemPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PunchListItem(Base, TimestampMixin, AuditMixin):
    """Punch list item for tracking construction deficiencies."""
    __tablename__ = "agcm_punch_list_items"
    _description = "Punch list items with status, priority, and assignment tracking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(PunchItemStatus, values_callable=lambda e: [m.value for m in e]),
        default=PunchItemStatus.OPEN,
        nullable=False,
        index=True,
    )

    priority = Column(
        Enum(PunchItemPriority, values_callable=lambda e: [m.value for m in e]),
        default=PunchItemPriority.MEDIUM,
        nullable=False,
    )

    location = Column(String(255), nullable=True)
    trade = Column(String(100), nullable=True)

    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    verified_date = Column(Date, nullable=True)

    verified_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    photo_before_url = Column(String(500), nullable=True)
    photo_after_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships

    __table_args__ = (
        Index("ix_agcm_punch_project_status", "project_id", "status"),
        Index("ix_agcm_punch_company", "company_id"),
    )
