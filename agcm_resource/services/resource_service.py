"""Resource service - business logic for workers, equipment, timesheets, assignments"""

import logging
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from addons.agcm_resource.models.worker import Worker
from addons.agcm_resource.models.equipment import Equipment
from addons.agcm_resource.models.timesheet import Timesheet, TimesheetStatus
from addons.agcm_resource.models.equipment_assignment import EquipmentAssignment
from addons.agcm_resource.schemas.resource import (
    WorkerCreate, WorkerUpdate,
    EquipmentCreate, EquipmentUpdate,
    TimesheetCreate, TimesheetUpdate,
    EquipmentAssignmentCreate, EquipmentAssignmentUpdate,
)
from addons.agcm_resource.services.sequence_service import next_sequence

logger = logging.getLogger(__name__)


class ResourceService:
    """Handles CRUD and business logic for resource models."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # WORKER CRUD
    # =========================================================================

    def list_workers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        trade: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Worker).filter(Worker.company_id == self.company_id)

        if status:
            query = query.filter(Worker.status == status)
        if trade:
            query = query.filter(Worker.trade.ilike(f"%{trade}%"))
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Worker.first_name.ilike(term))
                | (Worker.last_name.ilike(term))
                | (Worker.full_name.ilike(term))
                | (Worker.sequence_name.ilike(term))
                | (Worker.trade.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Worker.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "results": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }

    def get_worker(self, worker_id: int) -> Optional[Worker]:
        return (
            self.db.query(Worker)
            .filter(Worker.id == worker_id, Worker.company_id == self.company_id)
            .first()
        )

    def create_worker(self, data: WorkerCreate) -> Worker:
        worker = Worker(
            company_id=self.company_id,
            **data.model_dump(exclude_unset=True),
        )
        # Auto-generate full_name if not provided
        if not worker.full_name:
            worker.full_name = f"{worker.first_name} {worker.last_name}"
        worker.sequence_name = next_sequence(self.db, Worker, self.company_id)
        worker.created_by = self.user_id
        self.db.add(worker)
        self.db.commit()
        self.db.refresh(worker)
        return worker

    def update_worker(self, worker_id: int, data: WorkerUpdate) -> Optional[Worker]:
        worker = self.get_worker(worker_id)
        if not worker:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(worker, key, value)
        # Recompute full_name if first or last name changed
        if "first_name" in update_data or "last_name" in update_data:
            worker.full_name = f"{worker.first_name} {worker.last_name}"
        worker.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(worker)
        return worker

    def delete_worker(self, worker_id: int) -> bool:
        worker = self.get_worker(worker_id)
        if not worker:
            return False
        self.db.delete(worker)
        self.db.commit()
        return True

    # =========================================================================
    # EQUIPMENT CRUD
    # =========================================================================

    def list_equipment(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        equipment_type: Optional[str] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Equipment).filter(Equipment.company_id == self.company_id)

        if status:
            query = query.filter(Equipment.status == status)
        if equipment_type:
            query = query.filter(Equipment.equipment_type.ilike(f"%{equipment_type}%"))
        if project_id:
            query = query.filter(Equipment.current_project_id == project_id)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Equipment.name.ilike(term))
                | (Equipment.sequence_name.ilike(term))
                | (Equipment.equipment_type.ilike(term))
                | (Equipment.make.ilike(term))
                | (Equipment.serial_number.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Equipment.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "results": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }

    def get_equipment(self, equipment_id: int) -> Optional[Equipment]:
        return (
            self.db.query(Equipment)
            .filter(Equipment.id == equipment_id, Equipment.company_id == self.company_id)
            .first()
        )

    def create_equipment(self, data: EquipmentCreate) -> Equipment:
        equipment = Equipment(
            company_id=self.company_id,
            **data.model_dump(exclude_unset=True),
        )
        equipment.sequence_name = next_sequence(self.db, Equipment, self.company_id)
        equipment.created_by = self.user_id
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def update_equipment(self, equipment_id: int, data: EquipmentUpdate) -> Optional[Equipment]:
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(equipment, key, value)
        equipment.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def delete_equipment(self, equipment_id: int) -> bool:
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return False
        self.db.delete(equipment)
        self.db.commit()
        return True

    # =========================================================================
    # TIMESHEET CRUD
    # =========================================================================

    def _calculate_costs(self, timesheet: Timesheet):
        """Auto-calculate costs based on worker rates."""
        worker = (
            self.db.query(Worker)
            .filter(Worker.id == timesheet.worker_id, Worker.company_id == self.company_id)
            .first()
        )
        if worker:
            timesheet.regular_cost = timesheet.regular_hours * worker.hourly_rate
            timesheet.overtime_cost = timesheet.overtime_hours * worker.overtime_rate * 1.5
            double_cost = timesheet.double_time_hours * worker.hourly_rate * 2
            timesheet.total_hours = (
                timesheet.regular_hours + timesheet.overtime_hours + timesheet.double_time_hours
            )
            timesheet.total_cost = timesheet.regular_cost + timesheet.overtime_cost + double_cost
        else:
            timesheet.total_hours = (
                timesheet.regular_hours + timesheet.overtime_hours + timesheet.double_time_hours
            )

    def list_timesheets(
        self,
        page: int = 1,
        page_size: int = 20,
        worker_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = (
            self.db.query(Timesheet)
            .options(joinedload(Timesheet.worker), joinedload(Timesheet.project))
            .filter(Timesheet.company_id == self.company_id)
        )

        if worker_id:
            query = query.filter(Timesheet.worker_id == worker_id)
        if project_id:
            query = query.filter(Timesheet.project_id == project_id)
        if status:
            query = query.filter(Timesheet.status == status)
        if date_from:
            query = query.filter(Timesheet.date >= date_from)
        if date_to:
            query = query.filter(Timesheet.date <= date_to)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Timesheet.sequence_name.ilike(term))
                | (Timesheet.task_description.ilike(term))
                | (Timesheet.location.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Timesheet.date.desc(), Timesheet.id.desc()).offset(skip).limit(page_size).all()

        # Enrich with worker/project names
        enriched = []
        for ts in items:
            ts_dict = {
                "id": ts.id,
                "company_id": ts.company_id,
                "sequence_name": ts.sequence_name,
                "worker_id": ts.worker_id,
                "project_id": ts.project_id,
                "date": ts.date,
                "regular_hours": ts.regular_hours,
                "overtime_hours": ts.overtime_hours,
                "double_time_hours": ts.double_time_hours,
                "total_hours": ts.total_hours,
                "regular_cost": ts.regular_cost,
                "overtime_cost": ts.overtime_cost,
                "total_cost": ts.total_cost,
                "clock_in": ts.clock_in,
                "clock_out": ts.clock_out,
                "status": ts.status.value if hasattr(ts.status, 'value') else ts.status,
                "approved_by": ts.approved_by,
                "approved_date": ts.approved_date,
                "task_description": ts.task_description,
                "location": ts.location,
                "notes": ts.notes,
                "created_at": ts.created_at,
                "updated_at": ts.updated_at,
                "worker_name": None,
                "project_name": None,
            }
            if ts.worker:
                ts_dict["worker_name"] = getattr(ts.worker, "full_name", None) or f"{getattr(ts.worker, 'first_name', '')} {getattr(ts.worker, 'last_name', '')}"
            if ts.project:
                ts_dict["project_name"] = getattr(ts.project, "name", None)
            enriched.append(ts_dict)

        return {
            "items": enriched,
            "results": enriched,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }

    def get_timesheet(self, timesheet_id: int) -> Optional[Timesheet]:
        return (
            self.db.query(Timesheet)
            .filter(Timesheet.id == timesheet_id, Timesheet.company_id == self.company_id)
            .first()
        )

    def create_timesheet(self, data: TimesheetCreate) -> Timesheet:
        timesheet = Timesheet(
            company_id=self.company_id,
            **data.model_dump(exclude_unset=True),
        )
        timesheet.sequence_name = next_sequence(self.db, Timesheet, self.company_id)
        timesheet.status = TimesheetStatus.DRAFT
        self._calculate_costs(timesheet)
        timesheet.created_by = self.user_id
        self.db.add(timesheet)
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def update_timesheet(self, timesheet_id: int, data: TimesheetUpdate) -> Optional[Timesheet]:
        timesheet = self.get_timesheet(timesheet_id)
        if not timesheet:
            return None
        if timesheet.status in (TimesheetStatus.APPROVED,):
            return None  # Cannot edit approved timesheets
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(timesheet, key, value)
        self._calculate_costs(timesheet)
        timesheet.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def delete_timesheet(self, timesheet_id: int) -> bool:
        timesheet = self.get_timesheet(timesheet_id)
        if not timesheet:
            return False
        if timesheet.status in (TimesheetStatus.APPROVED,):
            return False
        self.db.delete(timesheet)
        self.db.commit()
        return True

    def submit_timesheet(self, timesheet_id: int) -> Optional[Timesheet]:
        timesheet = self.get_timesheet(timesheet_id)
        if not timesheet:
            return None
        if timesheet.status != TimesheetStatus.DRAFT:
            return None
        timesheet.status = TimesheetStatus.SUBMITTED
        timesheet.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def approve_timesheet(self, timesheet_id: int) -> Optional[Timesheet]:
        timesheet = self.get_timesheet(timesheet_id)
        if not timesheet:
            return None
        if timesheet.status != TimesheetStatus.SUBMITTED:
            return None
        timesheet.status = TimesheetStatus.APPROVED
        timesheet.approved_by = self.user_id
        timesheet.approved_date = date.today()
        timesheet.updated_by = self.user_id

        # Post labor cost to budget
        if timesheet.project_id and timesheet.total_cost:
            try:
                from addons.agcm.services.budget_posting import post_to_budget
                post_to_budget(
                    self.db, timesheet.project_id, self.company_id,
                    "actual_amount", timesheet.total_cost,
                    description="Labor (Timesheets)",
                )
            except ImportError:
                pass

        self.db.commit()
        self.db.refresh(timesheet)

        # Notify worker of approval
        try:
            from addons.agcm.services.notify import notify_event
            notify_event(
                self.db, "approved", "timesheet", timesheet.id, self.user_id,
                context={"date": str(timesheet.date)},
                recipient_ids=[timesheet.created_by] if timesheet.created_by else [],
                company_id=self.company_id,
            )
        except ImportError:
            pass

        return timesheet

    def reject_timesheet(self, timesheet_id: int) -> Optional[Timesheet]:
        timesheet = self.get_timesheet(timesheet_id)
        if not timesheet:
            return None
        if timesheet.status != TimesheetStatus.SUBMITTED:
            return None
        timesheet.status = TimesheetStatus.REJECTED
        timesheet.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    # =========================================================================
    # EQUIPMENT ASSIGNMENT CRUD
    # =========================================================================

    def list_equipment_assignments(
        self,
        page: int = 1,
        page_size: int = 20,
        equipment_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = (
            self.db.query(EquipmentAssignment)
            .options(joinedload(EquipmentAssignment.equipment), joinedload(EquipmentAssignment.project))
            .filter(EquipmentAssignment.company_id == self.company_id)
        )

        if equipment_id:
            query = query.filter(EquipmentAssignment.equipment_id == equipment_id)
        if project_id:
            query = query.filter(EquipmentAssignment.project_id == project_id)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(EquipmentAssignment.assigned_date.desc()).offset(skip).limit(page_size).all()

        enriched = []
        for ea in items:
            ea_dict = {
                "id": ea.id,
                "company_id": ea.company_id,
                "equipment_id": ea.equipment_id,
                "project_id": ea.project_id,
                "assigned_date": ea.assigned_date,
                "return_date": ea.return_date,
                "daily_rate": ea.daily_rate,
                "total_days": ea.total_days,
                "total_cost": ea.total_cost,
                "notes": ea.notes,
                "created_at": ea.created_at,
                "updated_at": ea.updated_at,
                "equipment_name": None,
                "project_name": None,
            }
            if ea.equipment:
                ea_dict["equipment_name"] = getattr(ea.equipment, "name", None)
            if ea.project:
                ea_dict["project_name"] = getattr(ea.project, "name", None)
            enriched.append(ea_dict)

        return {
            "items": enriched,
            "results": enriched,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }

    def get_equipment_assignment(self, assignment_id: int) -> Optional[EquipmentAssignment]:
        return (
            self.db.query(EquipmentAssignment)
            .filter(
                EquipmentAssignment.id == assignment_id,
                EquipmentAssignment.company_id == self.company_id,
            )
            .first()
        )

    def create_equipment_assignment(self, data: EquipmentAssignmentCreate) -> EquipmentAssignment:
        assignment = EquipmentAssignment(
            company_id=self.company_id,
            **data.model_dump(exclude_unset=True),
        )
        # Auto-calculate total_cost if total_days and daily_rate are set
        if assignment.total_days and assignment.daily_rate:
            assignment.total_cost = assignment.total_days * assignment.daily_rate
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def update_equipment_assignment(
        self, assignment_id: int, data: EquipmentAssignmentUpdate
    ) -> Optional[EquipmentAssignment]:
        assignment = self.get_equipment_assignment(assignment_id)
        if not assignment:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(assignment, key, value)
        if assignment.total_days and assignment.daily_rate:
            assignment.total_cost = assignment.total_days * assignment.daily_rate
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete_equipment_assignment(self, assignment_id: int) -> bool:
        assignment = self.get_equipment_assignment(assignment_id)
        if not assignment:
            return False
        self.db.delete(assignment)
        self.db.commit()
        return True

    def calculate_utilization(self, equipment_id: int) -> dict:
        """Calculate utilization stats for a piece of equipment."""
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return {"error": "Equipment not found"}

        assignments = (
            self.db.query(EquipmentAssignment)
            .filter(
                EquipmentAssignment.equipment_id == equipment_id,
                EquipmentAssignment.company_id == self.company_id,
            )
            .all()
        )

        total_assignments = len(assignments)
        total_days = sum(a.total_days for a in assignments)
        total_cost = sum(a.total_cost for a in assignments)
        active_assignments = sum(1 for a in assignments if a.return_date is None)

        return {
            "equipment_id": equipment_id,
            "equipment_name": equipment.name,
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
            "total_days_used": total_days,
            "total_cost": total_cost,
            "status": equipment.status.value if hasattr(equipment.status, 'value') else equipment.status,
        }
