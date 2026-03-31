"""Equipment model - equipment register for construction projects"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class EquipmentStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Equipment(Base, TimestampMixin, AuditMixin):
    """
    Construction equipment register.

    Tracks equipment details, status, ownership, rates, and maintenance schedule.
    """
    __tablename__ = "agcm_equipment"
    _description = "Construction equipment register"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Sequence
    sequence_name = Column(String(50), nullable=True)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    equipment_type = Column(String(100), nullable=False)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    serial_number = Column(String(100), nullable=True)
    license_plate = Column(String(50), nullable=True)

    # Status
    status = Column(
        Enum(EquipmentStatus, values_callable=lambda e: [m.value for m in e]),
        default=EquipmentStatus.AVAILABLE,
        nullable=False,
    )

    # Ownership & rates
    ownership_type = Column(String(50), default="owned", nullable=False)
    daily_rate = Column(Float, default=0, nullable=False)
    hourly_rate = Column(Float, default=0, nullable=False)

    # Current assignment
    current_project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_location = Column(String(255), nullable=True)

    # Maintenance
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    current_project = relationship("agcm_projects", foreign_keys=[current_project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_equipment_company_status", "company_id", "status"),
    )
