"""Task model - individual schedulable tasks"""

import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, Float, ForeignKey, Integer, String, Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin, AuditMixin


class TaskType(str, enum.Enum):
    TASK = "task"
    MILESTONE = "milestone"
    START_MILESTONE = "start_milestone"
    FINISH_MILESTONE = "finish_milestone"


class WorkType(str, enum.Enum):
    WORK = "work"
    DELIVERY = "delivery"
    INSPECTION = "inspection"
    ROADBLOCK = "roadblock"
    SAFETY = "safety"
    DOWNTIME = "downtime"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


class Task(Base, TimestampMixin, AuditMixin):
    """
    Individual task within a schedule.

    Supports planned/actual dates, progress tracking, float calculations,
    and critical path flagging.
    """
    __tablename__ = "agcm_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    sequence_name = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    task_type = Column(
        Enum(TaskType, values_callable=lambda e: [m.value for m in e]),
        default=TaskType.TASK,
        nullable=False,
    )
    work_type = Column(
        Enum(WorkType, values_callable=lambda e: [m.value for m in e]),
        default=WorkType.WORK,
        nullable=False,
    )
    status = Column(
        Enum(TaskStatus, values_callable=lambda e: [m.value for m in e]),
        default=TaskStatus.TODO,
        nullable=False,
        index=True,
    )

    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)

    duration_days = Column(Integer, default=0, nullable=False)
    progress = Column(Integer, default=0, nullable=False)

    total_float = Column(Float, default=0, nullable=False)
    free_float = Column(Float, default=0, nullable=False)
    is_critical = Column(Boolean, default=False, nullable=False)

    wbs_id = Column(
        Integer,
        ForeignKey("agcm_wbs.id", ondelete="SET NULL"),
        nullable=True,
    )

    schedule_id = Column(
        Integer,
        ForeignKey("agcm_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    schedule = relationship("Schedule", foreign_keys=[schedule_id], back_populates="tasks")
    wbs = relationship("WBS", foreign_keys=[wbs_id], lazy="select")
    assignee = relationship("User", foreign_keys=[assigned_to], lazy="select")
    project = relationship("Project", foreign_keys=[project_id], lazy="select")

    predecessors = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.successor_id",
        back_populates="successor",
        cascade="all, delete-orphan",
    )
    successors = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.predecessor_id",
        back_populates="predecessor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agcm_tasks_project_schedule", "project_id", "schedule_id"),
        Index("ix_agcm_tasks_company", "company_id"),
    )
