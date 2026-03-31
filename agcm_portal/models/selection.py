"""Selection models - material/finish choices for clients"""

import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class SelectionStatus(str, enum.Enum):
    PENDING = "pending"
    PRESENTED = "presented"
    APPROVED = "approved"
    REJECTED = "rejected"


class Selection(Base, TimestampMixin, AuditMixin):
    """Material/finish selection for client approval."""

    __tablename__ = "agcm_selections"

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

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    status = Column(
        Enum(
            SelectionStatus,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=SelectionStatus.PENDING,
        nullable=False,
    )

    due_date = Column(Date, nullable=True)
    decided_date = Column(Date, nullable=True)

    budget_amount = Column(Float, default=0)
    selected_amount = Column(Float, default=0)
    budget_impact = Column(Float, default=0)

    decided_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    options = relationship(
        "SelectionOption",
        back_populates="selection",
        cascade="all, delete-orphan",
        order_by="SelectionOption.display_order",
    )

    __table_args__ = (
        Index("ix_agcm_selection_project_status", "project_id", "status"),
    )


class SelectionOption(Base, TimestampMixin):
    """Individual option within a selection."""

    __tablename__ = "agcm_selection_options"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    selection_id = Column(
        Integer,
        ForeignKey("agcm_selections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0)
    unit = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    spec_url = Column(String(500), nullable=True)
    is_recommended = Column(Boolean, default=False)
    is_selected = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    # Relationships
    selection = relationship("Selection", back_populates="options")
