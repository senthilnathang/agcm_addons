"""Expense model - project expenses with line items"""

import enum

from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin


class ExpenseStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"


class Expense(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ActivityMixin):
    """Project expense with line items."""

    __tablename__ = "agcm_expenses"
    _description = "Project expenses with line items and approval workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)
    vendor = Column(String(255), nullable=True)

    status = Column(
        Enum(ExpenseStatus, values_callable=lambda e: [m.value for m in e]),
        default=ExpenseStatus.DRAFT,
        nullable=False,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")

    lines = relationship(
        "ExpenseLine",
        back_populates="expense",
        cascade="all, delete-orphan",
        order_by="ExpenseLine.id",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_exp_project_status", "project_id", "status"),
        Index("ix_agcm_exp_company", "company_id"),
    )


class ExpenseLine(Base, TimestampMixin):
    """Line item for an expense."""

    __tablename__ = "agcm_expense_lines"
    _description = "Expense line items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    expense_id = Column(
        Integer,
        ForeignKey("agcm_expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50), nullable=True)
    unit_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)

    cost_code_id = Column(
        Integer,
        ForeignKey("agcm_cost_codes.id", ondelete="SET NULL"),
        nullable=True,
    )

    category = Column(String(100), nullable=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    expense = relationship("Expense", back_populates="lines")

    __table_args__ = (Index("ix_agcm_exl_expense", "expense_id"),)
