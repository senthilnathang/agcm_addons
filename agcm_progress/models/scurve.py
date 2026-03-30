"""S-Curve model for periodic progress snapshots"""

from sqlalchemy import (
    Column, Date, Float, ForeignKey, Index, Integer, UniqueConstraint,
)

from app.db.base import Base
from app.models.base import TimestampMixin


class SCurveData(Base, TimestampMixin):
    """Periodic progress snapshot for S-curve visualization."""

    __tablename__ = "agcm_scurve_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False)
    planned_physical_pct = Column(Float, default=0, nullable=False)
    actual_physical_pct = Column(Float, default=0, nullable=False)
    revised_physical_pct = Column(Float, default=0, nullable=False)
    planned_financial_pct = Column(Float, default=0, nullable=False)
    actual_financial_pct = Column(Float, default=0, nullable=False)
    manpower_progress_pct = Column(Float, default=0, nullable=False)
    machinery_progress_pct = Column(Float, default=0, nullable=False)
    schedule_days_ahead = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "date", name="uq_agcm_scurve_project_date"),
        Index("ix_agcm_scurve_data_company", "company_id"),
    )
