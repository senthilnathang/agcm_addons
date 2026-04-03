"""ProjectMember model — per-project role assignment for users."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectRole(str, enum.Enum):
    OWNER = "owner"       # Full access, can manage members
    MANAGER = "manager"   # Full CRUD on project data
    MEMBER = "member"     # Create/edit own items, view all
    VIEWER = "viewer"     # Read-only access


class ProjectMember(Base):
    """Per-project user membership with role-based access."""

    __tablename__ = "agcm_project_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(
        Enum(ProjectRole, values_callable=lambda e: [m.value for m in e]),
        default=ProjectRole.MEMBER.value,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("ix_agcm_pm_project_user", "project_id", "user_id", unique=True),
        Index("ix_agcm_pm_user", "user_id"),
        Index("ix_agcm_pm_company", "company_id"),
    )
