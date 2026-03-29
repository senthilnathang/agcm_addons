"""ManPower model - daily workforce tracking"""

from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class ManPower(Base, TimestampMixin, AuditMixin):
    """
    Manpower entry for a daily log.

    Tracks workers, hours, and contractor/vendor per activity.
    total_hours = number_of_workers * number_of_hours (computed).
    """
    __tablename__ = "agcm_manpower"
    _description = "Daily manpower entries tracking workers and hours per contractor"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)  # Comments
    location = Column(String(255), nullable=True)

    # Worker data
    number_of_workers = Column(Integer, default=0, nullable=False)
    number_of_hours = Column(Float, default=0.0, nullable=False)
    total_hours = Column(Float, default=0.0, nullable=False)

    # Vendor/Contractor
    partner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Daily log link
    dailylog_id = Column(
        Integer,
        ForeignKey("agcm_daily_activity_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project link (denormalized for convenience)
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Copy tracking
    copy_id = Column(
        Integer,
        ForeignKey("agcm_manpower.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    partner = relationship("User", foreign_keys=[partner_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="manpower_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_manpower_dailylog", "dailylog_id"),
    )

    def compute_total_hours(self):
        """Compute total_hours = workers * hours"""
        if self.number_of_hours and self.number_of_workers:
            self.total_hours = self.number_of_hours * self.number_of_workers
        else:
            self.total_hours = 0.0
