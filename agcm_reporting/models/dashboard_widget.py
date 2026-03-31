"""Dashboard layout and widget models"""

import enum

from sqlalchemy import (
    Boolean, Column, Enum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class WidgetType(str, enum.Enum):
    KPI_CARD = "kpi_card"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    PROGRESS_BAR = "progress_bar"
    STAT_GROUP = "stat_group"


class AGCMDashboardLayout(Base, TimestampMixin, AuditMixin):
    """Saved dashboard configuration."""

    __tablename__ = "agcm_dashboard_layouts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    layout_type = Column(String(50), default="executive")  # executive, project, financial
    is_default = Column(Boolean, default=False)

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    widgets = relationship(
        "AGCMDashboardWidget",
        back_populates="layout",
        cascade="all, delete-orphan",
        order_by="AGCMDashboardWidget.display_order",
    )


class AGCMDashboardWidget(Base, TimestampMixin):
    """Individual widget within a dashboard layout."""

    __tablename__ = "agcm_dashboard_widgets"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    layout_id = Column(
        Integer,
        ForeignKey("agcm_dashboard_layouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    widget_type = Column(
        Enum(
            WidgetType,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    title = Column(String(255), nullable=False)
    config = Column(Text, nullable=True)  # JSON widget configuration
    data_source = Column(String(100), nullable=False)

    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=6)
    height = Column(Integer, default=4)
    display_order = Column(Integer, default=0)

    # Relationships
    layout = relationship("agcm_dashboard_layouts", back_populates="widgets")
