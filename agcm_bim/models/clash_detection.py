"""Clash Detection - test configurations and individual clash results"""

import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
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
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class ClashTestStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ClashSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ClashStatus(str, enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ClashTest(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """
    Clash detection run configuration.

    Defines two models (or same model for self-clash) and test parameters.
    Test types: hard (physical overlap), soft (clearance zone),
    clearance (minimum distance), duplicate (identical elements).
    """

    __tablename__ = "agcm_clash_tests"
    _description = "Clash detection test configuration and run results"

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

    # Identifiers
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Models to compare
    model_a_id = Column(
        Integer,
        ForeignKey("agcm_bim_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_b_id = Column(
        Integer,
        ForeignKey("agcm_bim_models.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Test parameters
    test_type = Column(
        String(50), default="hard", nullable=False
    )  # hard, soft, clearance, duplicate
    tolerance = Column(Float, default=0.01, nullable=False)  # meters

    # Status & results
    status = Column(
        Enum(ClashTestStatus, values_callable=lambda e: [m.value for m in e]),
        default=ClashTestStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_clashes = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    major_count = Column(Integer, default=0, nullable=False)
    minor_count = Column(Integer, default=0, nullable=False)

    # Run info
    run_date = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    model_a = relationship("BIMModel", foreign_keys=[model_a_id], lazy="select")
    model_b = relationship("BIMModel", foreign_keys=[model_b_id], lazy="select")

    results = relationship(
        "ClashResult",
        back_populates="clash_test",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("ix_agcm_clash_test_project", "project_id"),
        Index("ix_agcm_clash_test_company", "company_id"),
        {"extend_existing": True},
    )


class ClashResult(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """
    Individual clash found during a clash test run.

    Each result represents an overlap or clearance violation between
    two IFC elements, with location, severity, and resolution tracking.
    """

    __tablename__ = "agcm_clash_results"
    _description = "Individual clash detection results with resolution workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    clash_test_id = Column(
        Integer,
        ForeignKey("agcm_clash_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers
    sequence_name = Column(String(50), nullable=True)

    # Element A
    element_a_id = Column(String(255), nullable=True)  # IFC GlobalId
    element_a_name = Column(String(255), nullable=True)
    element_a_type = Column(String(100), nullable=True)  # IfcWall, IfcPipe, etc.

    # Element B
    element_b_id = Column(String(255), nullable=True)
    element_b_name = Column(String(255), nullable=True)
    element_b_type = Column(String(100), nullable=True)

    # Classification
    severity = Column(
        Enum(ClashSeverity, values_callable=lambda e: [m.value for m in e]),
        default=ClashSeverity.MINOR,
        nullable=False,
    )
    status = Column(
        Enum(ClashStatus, values_callable=lambda e: [m.value for m in e]),
        default=ClashStatus.NEW,
        nullable=False,
    )

    # Location
    clash_point = Column(Text, nullable=True)  # JSON {x, y, z}
    distance = Column(Float, nullable=True)  # overlap distance in meters
    description = Column(Text, nullable=True)  # auto-generated description

    # Visual
    screenshot_url = Column(String(500), nullable=True)
    viewpoint_id = Column(
        Integer,
        ForeignKey("agcm_bim_viewpoints.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Resolution workflow
    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_date = Column(Date, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    clash_test = relationship(
        "ClashTest",
        back_populates="results",
        foreign_keys=[clash_test_id],
        lazy="select",
    )
    viewpoint = relationship("BIMViewpoint", foreign_keys=[viewpoint_id], lazy="select")
    assignee = relationship("User", foreign_keys=[assigned_to], lazy="select")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="select")

    __table_args__ = (
        Index("ix_agcm_clash_result_test_status", "clash_test_id", "status"),
        Index("ix_agcm_clash_result_severity", "severity"),
        {"extend_existing": True},
    )
