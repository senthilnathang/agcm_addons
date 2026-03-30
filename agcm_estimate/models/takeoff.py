"""Takeoff models for plan measurement and quantity extraction."""

import enum

from sqlalchemy import (
    Column, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class MeasurementType(str, enum.Enum):
    LINEAR = "linear"
    AREA = "area"
    COUNT = "count"


class TakeoffSheet(Base, TimestampMixin, AuditMixin):
    """Uploaded plan sheet for digital takeoff measurements."""

    __tablename__ = "agcm_takeoff_sheets"

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
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(500), nullable=True)
    file_url = Column(String(1000), nullable=True)
    document_id = Column(Integer, nullable=True)
    page_number = Column(Integer, default=1)
    scale_factor = Column(Float, default=1.0)
    scale_unit = Column(String(20), default="ft")
    revision = Column(Integer, default=1)

    # Relationships
    measurements = relationship(
        "TakeoffMeasurement",
        back_populates="sheet",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class TakeoffMeasurement(Base, TimestampMixin):
    """Individual measurement on a takeoff sheet."""

    __tablename__ = "agcm_takeoff_measurements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sheet_id = Column(
        Integer,
        ForeignKey("agcm_takeoff_sheets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estimate_line_item_id = Column(
        Integer,
        ForeignKey("agcm_estimate_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    measurement_type = Column(
        Enum(MeasurementType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MeasurementType.LINEAR,
    )
    label = Column(String(255), nullable=True)
    value = Column(Float, default=0)
    unit = Column(String(20), default="ft")
    points_json = Column(Text, nullable=True)
    color = Column(String(20), default="#1890ff")
    layer = Column(String(100), nullable=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    sheet = relationship("TakeoffSheet", back_populates="measurements")
    estimate_line_item = relationship("EstimateLineItem", lazy="select")
