"""Worker model - workforce roster for construction projects"""

import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class WorkerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"


class SkillLevel(str, enum.Enum):
    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    MASTER = "master"
    FOREMAN = "foreman"
    SUPERINTENDENT = "superintendent"


class Worker(Base, TimestampMixin, AuditMixin):
    """
    Construction worker / workforce roster entry.

    Tracks personnel details, trade, skill level, rates, and certifications.
    """
    __tablename__ = "agcm_workers"
    _description = "Construction workforce roster"

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

    # Personal info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Status & classification
    status = Column(
        Enum(WorkerStatus, values_callable=lambda e: [m.value for m in e]),
        default=WorkerStatus.ACTIVE,
        nullable=False,
    )
    skill_level = Column(
        Enum(SkillLevel, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    trade = Column(String(100), nullable=True)

    # Rates
    hourly_rate = Column(Float, default=0, nullable=False)
    overtime_rate = Column(Float, default=0, nullable=False)

    # Certifications (JSON list stored as text)
    certifications = Column(Text, nullable=True)

    # Emergency contact
    emergency_contact = Column(String(255), nullable=True)
    emergency_phone = Column(String(50), nullable=True)

    # Employment
    hire_date = Column(Date, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_subcontractor = Column(Boolean, default=False, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships

    __table_args__ = (
        Index("ix_agcm_workers_company_status", "company_id", "status"),
    )
