"""Project model - top-level entity for AG CM module"""

import enum

from sqlalchemy import (
    Column, Date, Enum, Float, ForeignKey, Integer, String, Table,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin, SoftDeleteMixin


class ProjectStatus(str, enum.Enum):
    NEW = "new"
    PRECONSTRUCTION = "preconstruction"
    BIDDING = "bidding"
    AWARDED = "awarded"
    IN_PROGRESS = "inprogress"
    PUNCH_LIST = "punch_list"
    CLOSEOUT = "closeout"
    COMPLETED = "completed"
    WARRANTY = "warranty"
    ARCHIVED = "archived"


class ProjectOffice(str, enum.Enum):
    EAST = "east"
    SOUTH = "south"
    CENTRAL = "central"
    NORTH = "north"


# Many-to-many: Project <-> Contractors (res.partner equivalent = companies/contacts)
agcm_project_contractors = Table(
    "agcm_project_contractors",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("agcm_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("partner_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

# Many-to-many: Project <-> Users
agcm_project_users = Table(
    "agcm_project_users",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("agcm_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Construction project.

    Migrated from Odoo 'project' model.
    Key business logic:
    - Auto-generates sequence_name on create
    - Auto-computes lat/lng from ZIP + country
    - Owner is auto-added to user_ids
    - Non-management users only see projects they are assigned to
    """
    __tablename__ = "agcm_projects"
    _description = "Construction projects with location tracking and contractor management"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Company scoping
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers
    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    ref_number = Column(String(100), nullable=False)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Status
    status = Column(
        Enum(ProjectStatus),
        default=ProjectStatus.NEW,
        nullable=False,
        index=True,
    )

    # Trade
    trade_id = Column(
        Integer,
        ForeignKey("agcm_trades.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Owner
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    # Address
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    zip = Column(String(20), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Geolocation
    project_latitude = Column(Float, default=0.0, nullable=True)
    project_longitude = Column(Float, default=0.0, nullable=True)
    date_localization = Column(Date, nullable=True)

    # Office region
    agcm_office = Column(
        Enum(ProjectOffice),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    trade = relationship("agcm_trades", foreign_keys=[trade_id], lazy="select")
    owner = relationship("User", foreign_keys=[owner_id], lazy="select")

    partner_ids = relationship(
        "User",
        secondary=agcm_project_contractors,
        lazy="dynamic",
    )
    user_ids = relationship(
        "User",
        secondary=agcm_project_users,
        lazy="dynamic",
    )

    daily_activity_logs = relationship(
        "agcm_daily_activity_logs",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(agcm_daily_activity_logs.date)",
    )

    __table_args__ = (
        Index("ix_agcm_project_company_status", "company_id", "status"),
        Index("ix_agcm_project_owner", "owner_id"),
    )
