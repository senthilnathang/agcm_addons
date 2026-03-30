"""Dependency model - task relationships"""

import enum

from sqlalchemy import (
    Column, Enum, ForeignKey, Integer,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class DependencyType(str, enum.Enum):
    FS = "FS"  # Finish-to-Start
    SS = "SS"  # Start-to-Start
    FF = "FF"  # Finish-to-Finish
    SF = "SF"  # Start-to-Finish


class TaskDependency(Base, TimestampMixin):
    """
    Task dependency relationship.

    Defines predecessor/successor relationships between tasks
    with dependency type (FS, SS, FF, SF) and optional lag days.
    """
    __tablename__ = "agcm_task_dependencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    predecessor_id = Column(
        Integer,
        ForeignKey("agcm_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    successor_id = Column(
        Integer,
        ForeignKey("agcm_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    dependency_type = Column(
        Enum(DependencyType, values_callable=lambda e: [m.value for m in e]),
        default=DependencyType.FS,
        nullable=False,
    )

    lag_days = Column(Integer, default=0, nullable=False)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    predecessor = relationship(
        "Task",
        foreign_keys=[predecessor_id],
        back_populates="successors",
    )
    successor = relationship(
        "Task",
        foreign_keys=[successor_id],
        back_populates="predecessors",
    )

    __table_args__ = (
        Index("ix_agcm_task_deps_predecessor", "predecessor_id"),
        Index("ix_agcm_task_deps_successor", "successor_id"),
    )
