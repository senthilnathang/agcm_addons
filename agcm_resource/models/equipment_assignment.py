"""Equipment Assignment model - track equipment allocation to projects"""

from sqlalchemy import (
    Column, Date, Float, ForeignKey, Index, Integer, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class EquipmentAssignment(Base, TimestampMixin):
    """
    Equipment to project assignment tracking.

    Records which equipment is assigned to which project and for how long.
    """
    __tablename__ = "agcm_equipment_assignments"
    _description = "Equipment to project assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # References
    equipment_id = Column(
        Integer,
        ForeignKey("agcm_equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Assignment dates
    assigned_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)

    # Cost tracking
    daily_rate = Column(Float, default=0, nullable=False)
    total_days = Column(Integer, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    equipment = relationship("agcm_equipment", foreign_keys=[equipment_id], lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_equip_assign_equipment", "equipment_id"),
        Index("ix_agcm_equip_assign_project", "project_id"),
    )
