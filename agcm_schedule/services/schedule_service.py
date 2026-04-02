"""Schedule service - business logic for project scheduling"""

import logging
import re
from typing import Optional, List

from sqlalchemy.orm import Session

from addons.agcm_schedule.models.schedule import Schedule
from addons.agcm_schedule.models.wbs import WBS
from addons.agcm_schedule.models.task import Task
from addons.agcm_schedule.models.dependency import TaskDependency
from addons.agcm_schedule.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    WBSCreate,
    WBSUpdate,
    TaskCreate,
    TaskUpdate,
    DependencyCreate,
)

try:
    from app.core.cache import cache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Sequence config: (prefix, padding)
SEQUENCE_CONFIG = {
    "agcm_schedules": ("SCH", 5),
    "agcm_tasks": ("TSK", 5),
}


def _next_sequence(db: Session, model_class, company_id: int) -> str:
    """Generate next sequence_name for a model."""
    tablename = model_class.__tablename__
    config = SEQUENCE_CONFIG.get(tablename)
    if not config:
        return None

    prefix, padding = config

    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id)
        .filter(model_class.sequence_name.isnot(None))
        .order_by(model_class.id.desc())
        .first()
    )

    num = 1
    if last and last[0]:
        match = re.search(r"(\d+)$", last[0])
        if match:
            num = int(match.group(1)) + 1

    return f"{prefix}{num:0{padding}d}"


class ScheduleService:
    """
    Handles Schedule, WBS, Task, and Dependency CRUD and business logic.
    """

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # SCHEDULES
    # =========================================================================

    def list_schedules(self, project_id: int) -> List[Schedule]:
        """List all schedules for a project."""
        return (
            self.db.query(Schedule)
            .filter(
                Schedule.company_id == self.company_id,
                Schedule.project_id == project_id,
            )
            .order_by(Schedule.id.desc())
            .all()
        )

    def get_schedule(self, schedule_id: int) -> Optional[Schedule]:
        """Get a single schedule by ID."""
        return (
            self.db.query(Schedule)
            .filter(
                Schedule.id == schedule_id,
                Schedule.company_id == self.company_id,
            )
            .first()
        )

    def create_schedule(self, data: ScheduleCreate) -> Schedule:
        """Create a new schedule version."""
        # Determine version number
        existing_count = (
            self.db.query(Schedule)
            .filter(
                Schedule.company_id == self.company_id,
                Schedule.project_id == data.project_id,
            )
            .count()
        )

        schedule = Schedule(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Schedule, self.company_id),
            name=data.name,
            version=existing_count + 1,
            schedule_type=data.schedule_type,
            is_active=False,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def update_schedule(
        self, schedule_id: int, data: ScheduleUpdate
    ) -> Optional[Schedule]:
        """Update a schedule."""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(schedule, key, value)
        schedule.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def activate_schedule(self, schedule_id: int) -> Optional[Schedule]:
        """Activate a schedule, deactivating all others for the same project."""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None

        # Deactivate all schedules for this project
        self.db.query(Schedule).filter(
            Schedule.company_id == self.company_id,
            Schedule.project_id == schedule.project_id,
        ).update({"is_active": False})

        # Activate the target schedule
        schedule.is_active = True
        schedule.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule and all related data (cascade)."""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return False
        self.db.delete(schedule)
        self.db.commit()
        return True

    # =========================================================================
    # WBS
    # =========================================================================

    def list_wbs(self, schedule_id: int) -> List[WBS]:
        """List all WBS items for a schedule (flat)."""
        return (
            self.db.query(WBS)
            .filter(
                WBS.company_id == self.company_id,
                WBS.schedule_id == schedule_id,
            )
            .order_by(WBS.code)
            .all()
        )

    def get_wbs_tree(self, schedule_id: int) -> list:
        """Build hierarchical WBS tree for a schedule."""
        items = self.list_wbs(schedule_id)

        # Build lookup
        by_id = {}
        roots = []
        for item in items:
            node = {
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "parent_id": item.parent_id,
                "schedule_id": item.schedule_id,
                "project_id": item.project_id,
                "company_id": item.company_id,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "children": [],
            }
            by_id[item.id] = node

        for item in items:
            node = by_id[item.id]
            if item.parent_id and item.parent_id in by_id:
                by_id[item.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return roots

    def create_wbs(self, data: WBSCreate) -> WBS:
        """Create a WBS item."""
        wbs = WBS(
            code=data.code,
            name=data.name,
            parent_id=data.parent_id,
            schedule_id=data.schedule_id,
            project_id=data.project_id,
            company_id=self.company_id,
        )
        self.db.add(wbs)
        self.db.commit()
        self.db.refresh(wbs)
        return wbs

    def update_wbs(self, wbs_id: int, data: WBSUpdate) -> Optional[WBS]:
        """Update a WBS item."""
        wbs = (
            self.db.query(WBS)
            .filter(WBS.id == wbs_id, WBS.company_id == self.company_id)
            .first()
        )
        if not wbs:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(wbs, key, value)

        self.db.commit()
        self.db.refresh(wbs)
        return wbs

    def delete_wbs(self, wbs_id: int) -> bool:
        """Delete a WBS item."""
        wbs = (
            self.db.query(WBS)
            .filter(WBS.id == wbs_id, WBS.company_id == self.company_id)
            .first()
        )
        if not wbs:
            return False
        self.db.delete(wbs)
        self.db.commit()
        return True

    # =========================================================================
    # TASKS
    # =========================================================================

    def list_tasks(
        self,
        project_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> dict:
        """List tasks with filtering and pagination."""
        page_size = min(page_size, 200)
        query = self.db.query(Task).filter(Task.company_id == self.company_id)
        if not include_deleted:
            query = query.filter(Task.is_deleted == False)

        if project_id:
            query = query.filter(Task.project_id == project_id)
        if schedule_id:
            query = query.filter(Task.schedule_id == schedule_id)
        if status:
            query = query.filter(Task.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Task.name.ilike(search_term)) | (Task.sequence_name.ilike(search_term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Task.id.asc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_task(self, task_id: int, include_deleted: bool = False) -> Optional[Task]:
        """Get a single task by ID."""
        query = self.db.query(Task).filter(
            Task.id == task_id,
            Task.company_id == self.company_id,
        )
        if not include_deleted:
            query = query.filter(Task.is_deleted == False)
        return query.first()

    def create_task(self, data: TaskCreate) -> Task:
        """Create a new task."""
        task = Task(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Task, self.company_id),
            name=data.name,
            description=data.description,
            task_type=data.task_type,
            work_type=data.work_type,
            status=data.status,
            planned_start=data.planned_start,
            planned_end=data.planned_end,
            duration_days=data.duration_days,
            wbs_id=data.wbs_id,
            schedule_id=data.schedule_id,
            assigned_to=data.assigned_to,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        self._invalidate_task_cache(
            project_id=data.project_id, schedule_id=data.schedule_id
        )
        return task

    def update_task(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        """Update a task."""
        task = self.get_task(task_id)
        if not task:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        task.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(task)

        self._invalidate_task_cache(
            task_id=task.id, project_id=task.project_id, schedule_id=task.schedule_id
        )
        return task

    def update_progress(self, task_id: int, progress: int) -> Optional[Task]:
        """Update task progress (0-100)."""
        task = self.get_task(task_id)
        if not task:
            return None

        task.progress = max(0, min(100, progress))
        if task.progress == 100:
            task.status = "completed"
        task.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(task)

        self._invalidate_task_cache(
            task_id=task.id, project_id=task.project_id, schedule_id=task.schedule_id
        )
        return task

    def delete_task(self, task_id: int) -> bool:
        """Soft delete a task."""
        task = self.get_task(task_id)
        if not task:
            return False
        project_id = task.project_id
        schedule_id = task.schedule_id
        task.soft_delete(user_id=self.user_id)
        self.db.commit()

        self._invalidate_task_cache(
            task_id=task_id, project_id=project_id, schedule_id=schedule_id
        )
        return True

    def restore_task(self, task_id: int) -> Optional[Task]:
        """Restore a soft-deleted task."""
        task = self.get_task(task_id, include_deleted=True)
        if not task or not task.is_deleted:
            return None
        task.restore()
        self.db.commit()
        self.db.refresh(task)
        self._invalidate_task_cache(task_id=task.id, project_id=task.project_id)
        return task

    def _invalidate_task_cache(
        self, task_id: int = None, project_id: int = None, schedule_id: int = None
    ):
        """Invalidate task-related cache."""
        if not CACHE_AVAILABLE:
            return

        if task_id:
            cache.invalidate(f"agcm_schedule:task:{self.company_id}:{task_id}")
        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_schedule:tasks:project:{self.company_id}:{project_id}:*"
            )
        if schedule_id:
            cache.invalidate_pattern_distributed(
                f"agcm_schedule:tasks:schedule:{self.company_id}:{schedule_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_schedule:tasks:{self.company_id}:*")

    # =========================================================================
    # DEPENDENCIES
    # =========================================================================

    def list_dependencies(self, schedule_id: int) -> List[TaskDependency]:
        """List all dependencies for tasks in a schedule."""
        task_ids = (
            self.db.query(Task.id)
            .filter(
                Task.company_id == self.company_id,
                Task.schedule_id == schedule_id,
            )
            .subquery()
        )
        return (
            self.db.query(TaskDependency)
            .filter(
                TaskDependency.company_id == self.company_id,
                TaskDependency.predecessor_id.in_(task_ids),
            )
            .all()
        )

    def create_dependency(self, data: DependencyCreate) -> TaskDependency:
        """Create a task dependency."""
        dep = TaskDependency(
            predecessor_id=data.predecessor_id,
            successor_id=data.successor_id,
            dependency_type=data.dependency_type,
            lag_days=data.lag_days,
            company_id=self.company_id,
        )
        self.db.add(dep)
        self.db.commit()
        self.db.refresh(dep)
        return dep

    def delete_dependency(self, dep_id: int) -> bool:
        """Delete a dependency."""
        dep = (
            self.db.query(TaskDependency)
            .filter(
                TaskDependency.id == dep_id,
                TaskDependency.company_id == self.company_id,
            )
            .first()
        )
        if not dep:
            return False
        self.db.delete(dep)
        self.db.commit()
        return True

    # =========================================================================
    # GANTT DATA
    # =========================================================================

    def get_gantt_data(self, project_id: int, schedule_id: int) -> dict:
        """Get all data needed for Gantt chart rendering."""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.company_id == self.company_id,
                Task.project_id == project_id,
                Task.schedule_id == schedule_id,
            )
            .order_by(Task.planned_start.asc().nullslast(), Task.id.asc())
            .all()
        )

        task_ids = [t.id for t in tasks]

        dependencies = []
        if task_ids:
            dependencies = (
                self.db.query(TaskDependency)
                .filter(
                    TaskDependency.company_id == self.company_id,
                    TaskDependency.predecessor_id.in_(task_ids),
                )
                .all()
            )

        wbs_items = (
            self.db.query(WBS)
            .filter(
                WBS.company_id == self.company_id,
                WBS.schedule_id == schedule_id,
            )
            .order_by(WBS.code)
            .all()
        )

        return {
            "tasks": tasks,
            "dependencies": dependencies,
            "wbs_items": wbs_items,
        }
