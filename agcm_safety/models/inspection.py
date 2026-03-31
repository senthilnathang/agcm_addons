"""Inspection model - scheduled inspections with checklist items"""

import enum

from sqlalchemy import (
    Column, Date, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class InspectionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL = "conditional"


class SafetyInspection(Base, TimestampMixin, AuditMixin):
    """Scheduled inspection with checklist-based item tracking."""
    __tablename__ = "agcm_safety_inspections"
    _description = "Construction inspections with checklist items and results"

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

    template_id = Column(
        Integer,
        ForeignKey("agcm_checklist_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    inspector_name = Column(String(255), nullable=False)
    inspector_company = Column(String(255), nullable=True)
    inspection_type = Column(String(100), nullable=True)

    status = Column(
        Enum(InspectionStatus, values_callable=lambda e: [m.value for m in e]),
        default=InspectionStatus.SCHEDULED,
        nullable=False,
        index=True,
    )

    scheduled_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    overall_result = Column(String(50), nullable=True)

    # Relationships
    items = relationship(
        "SafetyInspectionItem",
        back_populates="inspection",
        cascade="all, delete-orphan",
        order_by="SafetyInspectionItem.display_order",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_insp_v2_project", "project_id"),
        Index("ix_agcm_insp_v2_status", "status"),
        Index("ix_agcm_insp_v2_company", "company_id"),
    )


class SafetyInspectionItem(Base, TimestampMixin):
    """Individual checklist item result within an inspection."""
    __tablename__ = "agcm_safety_inspection_items"
    _description = "Inspection checklist item results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    inspection_id = Column(
        Integer,
        ForeignKey("agcm_safety_inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description = Column(String(500), nullable=False)
    result = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    inspection = relationship("SafetyInspection", back_populates="items")

    __table_args__ = (
        Index("ix_agcm_insp_item_inspection", "inspection_id"),
    )
