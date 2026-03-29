"""Daily Activity Log model - central daily record per project"""

from sqlalchemy import (
    Column, Date, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class DailyActivityLog(Base, TimestampMixin, AuditMixin):
    """
    Daily activity log tied to a project.

    Migrated from Odoo 'daily.activity.log' model.
    Key business logic:
    - Auto-generates sequence_name on create
    - Date must be within 6 days of today
    - On create, auto-fetches weather forecast data for the project location
    - Supports "makelog" (copy) to duplicate a log with selective child copying
    """
    __tablename__ = "agcm_daily_activity_logs"
    _description = "Daily construction activity log entries"

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

    # Date
    date = Column(Date, nullable=False, index=True)

    # Project link
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Copy tracking (which log this was copied from)
    copy_id = Column(
        Integer,
        ForeignKey("agcm_daily_activity_logs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    project = relationship(
        "agcm_projects",
        back_populates="daily_activity_logs",
        lazy="select",
    )
    copied_from = relationship(
        "agcm_daily_activity_logs",
        remote_side="DailyActivityLog.id",
        foreign_keys=[copy_id],
        lazy="select",
    )

    # Child entity relationships (One2Many)
    weather_lines = relationship(
        "agcm_weather",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    weather_forecast_lines = relationship(
        "agcm_weather_forecasts",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    manpower_lines = relationship(
        "agcm_manpower",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    notes_lines = relationship(
        "agcm_notes",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    inspection_lines = relationship(
        "agcm_inspections",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    accident_lines = relationship(
        "agcm_accidents",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    visitor_lines = relationship(
        "agcm_visitors",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    safety_violation_lines = relationship(
        "agcm_safety_violations",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    delay_lines = relationship(
        "agcm_delays",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    deficiency_lines = relationship(
        "agcm_deficiencies",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )
    photo_lines = relationship(
        "agcm_photos",
        back_populates="dailylog",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agcm_dailylog_project_date", "project_id", "date"),
        Index("ix_agcm_dailylog_company", "company_id"),
    )
