"""Checklist template models - reusable inspection templates"""

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ChecklistTemplate(Base, TimestampMixin, AuditMixin):
    """Reusable inspection checklist template."""
    __tablename__ = "agcm_checklist_templates"
    _description = "Reusable inspection checklist templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    items = relationship(
        "ChecklistTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ChecklistTemplateItem.display_order",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_agcm_checklist_tpl_company", "company_id"),
    )


class ChecklistTemplateItem(Base, TimestampMixin):
    """Individual item within a checklist template."""
    __tablename__ = "agcm_checklist_template_items"
    _description = "Checklist template line items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    template_id = Column(
        Integer,
        ForeignKey("agcm_checklist_templates.id", ondelete="CASCADE"),
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
    required = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    template = relationship("ChecklistTemplate", back_populates="items")

    __table_args__ = (
        Index("ix_agcm_checklist_item_template", "template_id"),
    )
