"""Tests for the agcm_schedule module — Schedule, WBS, Task, TaskDependency models."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _schedule(load_model):
    return load_model("agcm_schedule", "schedule", "Schedule")


def _schedule_type(load_model):
    return load_model("agcm_schedule", "schedule", "ScheduleType")


def _wbs(load_model):
    return load_model("agcm_schedule", "wbs", "WBS")


def _task(load_model):
    return load_model("agcm_schedule", "task", "Task")


def _task_status(load_model):
    return load_model("agcm_schedule", "task", "TaskStatus")


def _task_type(load_model):
    return load_model("agcm_schedule", "task", "TaskType")


def _work_type(load_model):
    return load_model("agcm_schedule", "task", "WorkType")


def _dependency(load_model):
    return load_model("agcm_schedule", "dependency", "TaskDependency")


def _dep_type(load_model):
    return load_model("agcm_schedule", "dependency", "DependencyType")


# ---------------------------------------------------------------------------
# Schedule tests
# ---------------------------------------------------------------------------


class TestSchedule:
    def test_create_schedule(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        ScheduleType = _schedule_type(load_model)

        sched = Schedule(
            name="Baseline Schedule v1",
            version=1,
            schedule_type=ScheduleType.BASELINE,
            is_active=True,
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="SCH00001",
        )
        db.add(sched)
        db.flush()

        assert sched.id is not None
        assert sched.name == "Baseline Schedule v1"
        assert sched.schedule_type == ScheduleType.BASELINE

    def test_schedule_sequence(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)

        for i in range(1, 4):
            db.add(
                Schedule(
                    name=f"Schedule {i}",
                    project_id=project_ids[0],
                    company_id=company_id,
                    sequence_name=f"SCH{i:05d}",
                )
            )
        db.flush()

        scheds = (
            db.query(Schedule)
            .filter(Schedule.project_id == project_ids[0])
            .order_by(Schedule.id)
            .all()
        )
        assert scheds[0].sequence_name == "SCH00001"
        assert scheds[2].sequence_name == "SCH00003"

    def test_activate_schedule(self, db, load_model, project_ids, company_id):
        """Activating one schedule should allow deactivating others for same project."""
        Schedule = _schedule(load_model)

        s1 = Schedule(
            name="S1", project_id=project_ids[0], company_id=company_id, is_active=True
        )
        s2 = Schedule(
            name="S2", project_id=project_ids[0], company_id=company_id, is_active=False
        )
        db.add_all([s1, s2])
        db.flush()

        # Deactivate s1, activate s2 (simulating service logic)
        s1.is_active = False
        s2.is_active = True
        db.flush()

        assert s1.is_active is False
        assert s2.is_active is True

    def test_delete_schedule_cascades(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        WBS = _wbs(load_model)
        Task = _task(load_model)

        sched = Schedule(
            name="Cascade sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()

        wbs = WBS(
            code="1.0",
            name="Foundation",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(wbs)
        db.flush()

        task = Task(
            name="Excavation",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            wbs_id=wbs.id,
        )
        db.add(task)
        db.flush()
        wbs_id = wbs.id
        task_id = task.id

        db.delete(sched)
        db.flush()

        assert db.get(WBS, wbs_id) is None
        assert db.get(Task, task_id) is None


# ---------------------------------------------------------------------------
# WBS tests
# ---------------------------------------------------------------------------


class TestWBS:
    def test_create_wbs(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        WBS = _wbs(load_model)

        sched = Schedule(
            name="WBS sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()

        wbs = WBS(
            code="1.0",
            name="Sitework",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(wbs)
        db.flush()

        assert wbs.id is not None
        assert wbs.code == "1.0"
        assert wbs.name == "Sitework"

    def test_wbs_hierarchy(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        WBS = _wbs(load_model)

        sched = Schedule(
            name="Hierarchy sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()

        parent = WBS(
            code="1.0",
            name="Foundation",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(parent)
        db.flush()

        child = WBS(
            code="1.1",
            name="Excavation",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            parent_id=parent.id,
        )
        db.add(child)
        db.flush()

        assert child.parent_id == parent.id
        db.expire(parent)
        assert len(parent.children) == 1
        assert parent.children[0].code == "1.1"


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


class TestTask:
    def _make_schedule(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        sched = Schedule(
            name="Task sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()
        return sched

    def test_create_task(self, db, load_model, project_ids, company_id):
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)
        TaskType = _task_type(load_model)
        WorkType = _work_type(load_model)
        TaskStatus = _task_status(load_model)

        task = Task(
            name="Pour concrete slab",
            description="Ground floor slab pour",
            task_type=TaskType.TASK,
            work_type=WorkType.WORK,
            status=TaskStatus.TODO,
            planned_start=date(2026, 4, 1),
            planned_end=date(2026, 4, 10),
            duration_days=10,
            progress=0,
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="TSK00001",
        )
        db.add(task)
        db.flush()

        assert task.id is not None
        assert task.name == "Pour concrete slab"
        assert task.sequence_name == "TSK00001"
        assert task.duration_days == 10

    def test_task_sequence(self, db, load_model, project_ids, company_id):
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)

        for i in range(1, 4):
            db.add(
                Task(
                    name=f"Task {i}",
                    schedule_id=sched.id,
                    project_id=project_ids[0],
                    company_id=company_id,
                    sequence_name=f"TSK{i:05d}",
                )
            )
        db.flush()

        tasks = (
            db.query(Task).filter(Task.schedule_id == sched.id).order_by(Task.id).all()
        )
        assert tasks[0].sequence_name == "TSK00001"
        assert tasks[2].sequence_name == "TSK00003"

    def test_task_progress_update(self, db, load_model, project_ids, company_id):
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)
        TaskStatus = _task_status(load_model)

        task = Task(
            name="Progress task",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            progress=0,
        )
        db.add(task)
        db.flush()

        task.progress = 50
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = date(2026, 4, 2)
        db.flush()
        assert task.progress == 50

        task.progress = 100
        task.status = TaskStatus.COMPLETED
        task.actual_end = date(2026, 4, 12)
        db.flush()
        assert task.progress == 100
        assert task.status == TaskStatus.COMPLETED

    def test_list_tasks_filter_by_status(self, db, load_model, project_ids, company_id):
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)
        TaskStatus = _task_status(load_model)

        db.add(
            Task(
                name="T1",
                schedule_id=sched.id,
                project_id=project_ids[0],
                company_id=company_id,
                status=TaskStatus.TODO,
            )
        )
        db.add(
            Task(
                name="T2",
                schedule_id=sched.id,
                project_id=project_ids[0],
                company_id=company_id,
                status=TaskStatus.IN_PROGRESS,
            )
        )
        db.add(
            Task(
                name="T3",
                schedule_id=sched.id,
                project_id=project_ids[0],
                company_id=company_id,
                status=TaskStatus.TODO,
            )
        )
        db.flush()

        todos = (
            db.query(Task)
            .filter(Task.status == TaskStatus.TODO, Task.schedule_id == sched.id)
            .all()
        )
        assert len(todos) == 2

    def test_task_critical_path_flag(self, db, load_model, project_ids, company_id):
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)

        task = Task(
            name="Critical task",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            is_critical=True,
            total_float=0.0,
        )
        db.add(task)
        db.flush()

        assert task.is_critical is True
        assert task.total_float == 0.0

    def test_task_soft_delete(self, db, load_model, project_ids, company_id, user_id):
        """Test soft delete functionality for tasks."""
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)

        task = Task(
            name="Delete me",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(task)
        db.flush()

        assert task.is_deleted is False
        assert task.deleted_at is None

        task.soft_delete(user_id=user_id)
        db.flush()

        assert task.is_deleted is True
        assert task.deleted_at is not None
        assert task.deleted_by == user_id

    def test_task_restore(self, db, load_model, project_ids, company_id, user_id):
        """Test restore functionality for tasks."""
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)

        task = Task(
            name="Restore me",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(task)
        db.flush()

        task.soft_delete(user_id=user_id)
        db.flush()
        assert task.is_deleted is True

        task.restore()
        db.flush()
        assert task.is_deleted is False
        assert task.deleted_at is None
        assert task.deleted_by is None

    def test_soft_deleted_tasks_excluded_from_list(
        self, db, load_model, project_ids, company_id, user_id
    ):
        """Test that soft-deleted tasks are excluded from default queries."""
        sched = self._make_schedule(db, load_model, project_ids, company_id)
        Task = _task(load_model)

        task1 = Task(
            name="Active task",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        task2 = Task(
            name="Deleted task",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add_all([task1, task2])
        db.flush()

        task2.soft_delete(user_id=user_id)
        db.flush()

        active_tasks = (
            db.query(Task)
            .filter(
                Task.schedule_id == sched.id,
                Task.is_deleted == False,
            )
            .all()
        )

        assert len(active_tasks) == 1
        assert active_tasks[0].name == "Active task"


# ---------------------------------------------------------------------------
# Dependency tests
# ---------------------------------------------------------------------------


class TestTaskDependency:
    def test_create_dependency(self, db, load_model, project_ids, company_id):
        Schedule = _schedule(load_model)
        Task = _task(load_model)
        TaskDependency = _dependency(load_model)
        DependencyType = _dep_type(load_model)

        sched = Schedule(
            name="Dep sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()

        t1 = Task(
            name="Predecessor",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        t2 = Task(
            name="Successor",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add_all([t1, t2])
        db.flush()

        dep = TaskDependency(
            predecessor_id=t1.id,
            successor_id=t2.id,
            dependency_type=DependencyType.FS,
            lag_days=2,
            company_id=company_id,
        )
        db.add(dep)
        db.flush()

        assert dep.id is not None
        assert dep.dependency_type == DependencyType.FS
        assert dep.lag_days == 2

    def test_gantt_data(self, db, load_model, project_ids, company_id):
        """Simulate fetching gantt data: tasks + dependencies + WBS for a schedule."""
        Schedule = _schedule(load_model)
        Task = _task(load_model)
        WBS = _wbs(load_model)
        TaskDependency = _dependency(load_model)
        DependencyType = _dep_type(load_model)

        sched = Schedule(
            name="Gantt sched", project_id=project_ids[0], company_id=company_id
        )
        db.add(sched)
        db.flush()

        wbs = WBS(
            code="1.0",
            name="Phase 1",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(wbs)
        db.flush()

        t1 = Task(
            name="Gantt T1",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            wbs_id=wbs.id,
            planned_start=date(2026, 4, 1),
            planned_end=date(2026, 4, 5),
        )
        t2 = Task(
            name="Gantt T2",
            schedule_id=sched.id,
            project_id=project_ids[0],
            company_id=company_id,
            wbs_id=wbs.id,
            planned_start=date(2026, 4, 6),
            planned_end=date(2026, 4, 10),
        )
        db.add_all([t1, t2])
        db.flush()

        dep = TaskDependency(
            predecessor_id=t1.id,
            successor_id=t2.id,
            dependency_type=DependencyType.FS,
            company_id=company_id,
        )
        db.add(dep)
        db.flush()

        # Query gantt data
        tasks = db.query(Task).filter(Task.schedule_id == sched.id).all()
        deps = (
            db.query(TaskDependency)
            .filter(TaskDependency.predecessor_id.in_([t.id for t in tasks]))
            .all()
        )
        wbs_items = db.query(WBS).filter(WBS.schedule_id == sched.id).all()

        assert len(tasks) == 2
        assert len(deps) == 1
        assert len(wbs_items) == 1
