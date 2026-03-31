"""Report definition and schedule models"""

import enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ReportType(str, enum.Enum):
    FINANCIAL = "financial"
    SCHEDULE = "schedule"
    SAFETY = "safety"
    RESOURCE = "resource"
    CUSTOM = "custom"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class AGCMReportDefinition(Base, TimestampMixin, AuditMixin):
    """Saved report template with column/filter configuration."""

    __tablename__ = "agcm_report_definitions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    report_type = Column(
        Enum(
            ReportType,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ReportType.CUSTOM,
        nullable=False,
    )

    data_source = Column(String(100), nullable=False)
    columns = Column(Text, nullable=True)  # JSON array of column definitions
    filters = Column(Text, nullable=True)  # JSON saved filter state
    sort_by = Column(String(100), nullable=True)
    sort_order = Column(String(10), default="desc")
    group_by = Column(String(100), nullable=True)

    is_system = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=True)

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    schedules = relationship(
        "AGCMReportSchedule",
        back_populates="report",
        cascade="all, delete-orphan",
    )


class AGCMReportSchedule(Base, TimestampMixin):
    """Scheduled report delivery configuration."""

    __tablename__ = "agcm_report_schedules"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    report_id = Column(
        Integer,
        ForeignKey("agcm_report_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    schedule_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    recipients = Column(Text, nullable=True)  # JSON array of emails
    next_run = Column(DateTime(timezone=True), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    format = Column(
        Enum(
            ReportFormat,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ReportFormat.PDF,
        nullable=False,
    )

    # Relationships
    report = relationship("AGCMReportDefinition", back_populates="schedules")
