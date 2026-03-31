"""T&M Ticket model - Time and Material tracking"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class TMTicketStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    BILLED = "billed"
    VOID = "void"


class TMLineType(str, enum.Enum):
    LABOR = "labor"
    MATERIAL = "material"
    EQUIPMENT = "equipment"


class TMTicket(Base, TimestampMixin, AuditMixin):
    """Time and Material ticket for tracking extra work."""

    __tablename__ = "agcm_tm_tickets"
    _description = "Time and Material tickets"

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

    sequence_name = Column(String(50), nullable=True)
    ticket_number = Column(String(100), nullable=True)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(TMTicketStatus, values_callable=lambda e: [m.value for m in e]),
        default=TMTicketStatus.DRAFT,
        nullable=False,
    )

    change_order_id = Column(
        Integer,
        ForeignKey("agcm_change_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    vendor_name = Column(String(255), nullable=True)

    labor_total = Column(Float, default=0, nullable=False)
    material_total = Column(Float, default=0, nullable=False)
    equipment_total = Column(Float, default=0, nullable=False)
    markup_pct = Column(Float, default=0, nullable=False)
    markup_amount = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)

    submitted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    notes = Column(Text, nullable=True)

    # Relationships
    lines = relationship(
        "TMTicketLine",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agcm_tm_project", "project_id"),
        Index("ix_agcm_tm_company", "company_id"),
    )


class TMTicketLine(Base, TimestampMixin):
    """Line item for a T&M ticket."""

    __tablename__ = "agcm_tm_ticket_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    ticket_id = Column(
        Integer,
        ForeignKey("agcm_tm_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_type = Column(
        Enum(TMLineType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )

    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=0, nullable=False)
    unit = Column(String(50), nullable=True)
    unit_cost = Column(Float, default=0, nullable=False)
    total_cost = Column(Float, default=0, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    ticket = relationship("TMTicket", back_populates="lines")
