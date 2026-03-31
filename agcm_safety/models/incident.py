"""Incident report model - safety incident tracking"""

import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class IncidentSeverity(str, enum.Enum):
    NEAR_MISS = "near_miss"
    FIRST_AID = "first_aid"
    MEDICAL = "medical"
    LOST_TIME = "lost_time"
    FATALITY = "fatality"


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentReport(Base, TimestampMixin, AuditMixin):
    """Safety incident report with investigation tracking."""
    __tablename__ = "agcm_incident_reports"
    _description = "Safety incident reports with severity, investigation, and OSHA tracking"

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
    description = Column(Text, nullable=False)

    severity = Column(
        Enum(IncidentSeverity, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )

    status = Column(
        Enum(IncidentStatus, values_callable=lambda e: [m.value for m in e]),
        default=IncidentStatus.REPORTED,
        nullable=False,
        index=True,
    )

    incident_date = Column(Date, nullable=False)
    incident_time = Column(String(10), nullable=True)
    location = Column(String(255), nullable=True)

    injured_party = Column(String(255), nullable=True)
    injury_description = Column(Text, nullable=True)
    witness_names = Column(Text, nullable=True)

    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)

    reported_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    investigated_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    investigation_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    osha_recordable = Column(Boolean, default=False, nullable=False)
    days_lost = Column(Integer, default=0, nullable=False)

    photo_urls = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships

    __table_args__ = (
        Index("ix_agcm_incident_project", "project_id"),
        Index("ix_agcm_incident_severity", "severity"),
        Index("ix_agcm_incident_status", "status"),
        Index("ix_agcm_incident_company", "company_id"),
    )
