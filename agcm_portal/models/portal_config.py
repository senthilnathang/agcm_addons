"""Portal configuration model - per-project portal settings"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, ActivityMixin


class PortalConfig(Base, TimestampMixin, AuditMixin, ActivityMixin):
    """Per-project portal visibility settings."""

    __tablename__ = "agcm_portal_configs"

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
        unique=True,
        index=True,
    )

    client_portal_enabled = Column(Boolean, default=True)
    sub_portal_enabled = Column(Boolean, default=True)
    show_budget = Column(Boolean, default=False)
    show_schedule = Column(Boolean, default=True)
    show_documents = Column(Boolean, default=True)
    show_photos = Column(Boolean, default=True)
    show_daily_logs = Column(Boolean, default=False)
    welcome_message = Column(Text, nullable=True)

    # Relationships

    __table_args__ = {"extend_existing": True}
